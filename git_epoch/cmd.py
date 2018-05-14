import argparse
import datetime
import typing

import git

SECONDS_PER_DAY = 60*60*24
EPOCH_TAG_IDENTIFIER = 'git-epoch'


def _find_epochs(repo, days) -> typing.List[git.Commit]:
    """
    Determine development epochs as defined by having an interval of no
    commits longer than `days` long.

    :param repo:
        Repo to find epochs in.
    :param days:
        The number of days between commits to define seperate development
        epochs.
    """
    epoch_gap = SECONDS_PER_DAY * days
    commits = list(repo.iter_commits('master'))
    cron_commits = sorted(commits, key=lambda c: c.committed_date)
    last_commit = None
    epoch_commits = []
    for commit in cron_commits:
        if (
            last_commit
            and last_commit.committed_date + epoch_gap < commit.committed_date
        ):
            epoch_commits.append(commit)
        last_commit = commit
    return epoch_commits


def _get_date_tag(epoch_time):
    dt = datetime.datetime.fromtimestamp(epoch_time).date()
    return EPOCH_TAG_IDENTIFIER + '/' + str(dt)


def _tag_epochs(repo, epoch_commits):
    for commit in epoch_commits:
        try:
            repo.create_tag(
                _get_date_tag(commit.committed_date),
                ref=commit.hexsha
            )
        except git.exc.GitCommandError:
            pass


def _confirm_epochs(epoch_commits):
    print('Tags to be added:')
    for commit in epoch_commits:
        print(_get_date_tag(commit.committed_date) + ' ' + commit.hexsha)
    user_input = input('enter "yes" to confirm: ')
    return user_input == 'yes'


def create_tags(repo, days, force=False):
    epoch_commits = _find_epochs(repo, days)
    if force or _confirm_epochs(epoch_commits):
        _tag_epochs(repo, epoch_commits)
    else:
        print('Tagging aborted.')


def remove_tags(repo):
    deleted = []
    for tag in repo.tags:
        if tag.name.startswith(EPOCH_TAG_IDENTIFIER):
            deleted.append(tag.name)
            repo.delete_tag(tag)
    if deleted:
        print('git-epoch tags deleted locally.')
        print('To delete tags on remote run:')
        print('    `git push origin --delete {0}`'.format(' '.join(deleted)))


def main():
    """
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--delete', dest='delete', action='store_true')
    parser.add_argument('--epoch-gap', dest='days', default=14)
    args = parser.parse_args()
    repo = git.Repo()
    if args.delete:
        remove_tags(repo)
    else:
        create_tags(repo, args.days)


if __name__ == '__main__':
    main()
