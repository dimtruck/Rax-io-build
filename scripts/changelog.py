import argparse
from datetime import datetime
from launchpadlib import launchpad
import os
import re
import subprocess

parser = argparse.ArgumentParser(
    description='Create a changelog for a build')
parser.add_argument('first_branch', help="The first branch to compare.")
parser.add_argument('second_branch', help="The second branch to compare.")
parser.add_argument('--repo', default=".", help="The local repo to use.")
parser.add_argument('--project', default="Raxio", help=("The project for naming"
                                                        " the changelog."))
parser.add_argument('--launchpad_cache', default="/tmp/launchpad",
                    help="The cache directory for launchpad.")
parser.add_argument('--output', default=None, help=("Where to write the "
                                                    "changelog."))


def launchpad_auth(cachedir):
    return launchpad.Launchpad.login_anonymously('testing',
                                                 'production',
                                                 cachedir)


def git_short_log_cmd(first_branch, second_branch, delimiter=':::'):
    format = ("%%H%(delim)s%%an%(delim)s%%ad%(delim)s%%s"
              % dict(delim=delimiter))
    log = ['git', 'log', "--no-merges",
           '--pretty=format:%s' % format,
           "%s..%s" % (first_branch, second_branch)]
    return log


def git_commit_msg_cmd(sha):
    return ['git', 'log', '--format=%B', '-n', '1', sha]


def parse_gerrit_changeid(msg):
    change_id = re.compile(r'\s*Change-Id\s*:\s*(\S+)\s*$', flags=re.I)
    for match in re.finditer(change_id, msg):
        return match.group(1)


def get_gerrit_link(changeid):
    if changeid:
        return (changeid, "https://review.openstack.org/#q,%s,n,z" % changeid)


def parse_bug(msg):
    """
    github.com/openstack-infra/jeepyb/blob/master/jeepyb/cmd/update_bug.py """
    part1 = r'^[\t ]*(?P<prefix>[-\w]+)?[\s:]*'
    part2 = r'(?:\b(?:bug|lp)\b[\s#:]*)+'
    part3 = r'(?P<bug_number>\d+)\s*?$'
    regexp = part1 + part2 + part3
    matches = re.finditer(regexp, msg, flags=re.I | re.M)

    for match in matches:
        return (match.group('prefix'), match.group('bug_number'))


def get_launchpad_bug(launchpad, bug):
    if bug:
        prefix, number = bug
        return (prefix, number, launchpad.bugs[number].web_link)


def parse_bp(msg):
    blueprint = re.compile(r'\b(blueprint|bp)\b[ \t]*[#:]?[ \t]*(\S+)', re.I)
    for match in re.finditer(blueprint, msg):
        if match:
            return match.group(2)


def get_launchpad_bp(launchpad, bp):
    if bp:
        # blueprint api
        return (bp, 'https://blueprints.launchpad.net/solum/+spec/' + bp)


def parse_git_log(git_log, delimiter=":::"):
    fields = []
    for line in git_log.split('\n'):
        string = ('(.*)%(delim)s(.*)%(delim)s(.*)%(delim)s(.*)'
                  % dict(delim=delimiter))
        match = re.match(re.compile(string), line)
        if match:
            fields.append(dict(commit=match.group(1),
                               author=match.group(2),
                               date=match.group(3),
                               msg=match.group(4)))
        else:
            print "WARNING %s did not match!"
    return fields


def git_changelogs(repo, first, second):
    os.chdir(repo)
    git_log = subprocess.check_output(git_short_log_cmd(first, second))
    changelogs = parse_git_log(git_log)
    for changelog in changelogs:
        changelog['long_msg'] = subprocess.check_output(git_commit_msg_cmd(
            changelog['commit']))
    return changelogs


def add_launchpad_info(launchpad, changelogs):
    for changelog in changelogs:
        changelog['bug'] = get_launchpad_bug(launchpad,
                                             parse_bug(changelog['long_msg']))
        changelog['bp'] = get_launchpad_bp(launchpad,
                                           parse_bp(changelog['long_msg']))
        changelog['review'] = get_gerrit_link(
            parse_gerrit_changeid(changelog['long_msg']))
    return changelogs


def format_bug(bug):
    if bug:
        return ("\n%sbug: %s\n"
                "Bug-Url: %s" % bug)
    return ''


def format_bp(bp):
    if bp:
        return ("\nBlueprint: %s\n"
                "Blueprint-Url: %s" % bp)
    return ''


def format_gerrit_review(review):
    if review:
        return ("\nChange-Id: %s\n"
                "Gerrit-Review: %s" % review)
    return ''


def format_changelogs(changelogs):
    for changelog in changelogs:
        try:
            yield ("Commit: %s\n"
                 "Author: %s\n"
                 "Date: %s\n"
                 "Message: %s"
                 "%s"
                 "%s"
                 "%s\n\n"
                 % (changelog['commit'],
                    changelog['author'],
                    changelog['date'],
                    changelog['msg'],
                    format_bug(changelog['bug']),
                    format_bp(changelog['bp']),
                    format_gerrit_review(changelog['review'])))
        except Exception:
            yield str(changelog) + "\n\n"


def utcnow():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def main():
    args = parser.parse_args()
    launchconn = launchpad_auth(args.launchpad_cache)
    changelogs = add_launchpad_info(launchconn,
                                    git_changelogs(args.repo,
                                                   args.first_branch,
                                                   args.second_branch))
    formatted = format_changelogs(changelogs)

    previous_version = ("Previous-Version: %s"
                        % args.first_branch.split("/")[-1])  # remove path
    wrap = len(previous_version) * "*"
    header = ("%s\n"
              "%s Changelog\n"
              "Date: %s\n"
              "%s\n"
              "Current-Version: %s\n"
              "%s\n") % (wrap,
                         args.project,
                         utcnow(),
                         previous_version,
                         args.second_branch.split("/")[-1],  # remove path
                         wrap)
    if args.output:
        with open(args.output, 'w') as outfile:
            outfile.write(header)
            for changelog in formatted:
                outfile.write(changelog)
    else:
        print header
        for line in formatted:
            print line

if __name__ == "__main__":
    main()
