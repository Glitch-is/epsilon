import sys
import os
import argparse
import datetime
import shutil
from subprocess import Popen, PIPE

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, BASE_DIR)
import lib.judgelib as j
from lib.models import Submission, SubmissionQueue
import lib.models as models
from lib.yamllib import load, dump
from lib.queue import Submissions

SUBMISSION_WAIT = 1000  # ms
contest = None
CWD = os.getcwd()


def format_time(time):
    if isinstance(time, datetime.datetime):
        time = (time - contest["start"]).total_seconds()
    return '%02d:%02d' % (int(time // 60), int(time) % 60)


def do_list(opts, parser):
    if opts.type not in {'all', 'queue'}:
        parser.print_help()
        exit(0)

    db = models.get_db(j.DB_CONN_STRING)
    try:
        sess = db()

        if opts.type == 'all':
            subs = sess.query(Submission)
        elif opts.type == 'queue':
            subs = sess.query(Submission, SubmissionQueue).join(SubmissionQueue, Submission.id == SubmissionQueue.submission_id)

        if opts.team:
            subs = subs.filter(Submission.team == opts.team)
        if opts.problem:
            subs = subs.filter(Submission.problem == opts.problem)

        for item in subs.order_by(Submission.submitted).all():
            sub = item
            subq = None
            if opts.type == 'queue':
                sub = item[0]
                subq = item[1]

            sys.stdout.write('%d\t%s\t%s\t%s\t%s\t%s\n' % (sub.id, format_time(sub.submitted), sub.team, sub.problem, sub.verdict, '' if subq is None else subq.dequeued_at))

    finally:
        sess.close()


def do_checkout(opts, parser):
    sub = None
    if opts.id == 'next':
        sys.stdout.write('waiting for next submission...\n')

        with Submissions(j.DB_CONN_STRING, timeout=False) as subs:
            sub2 = next(subs)
            opts.id = sub2.id
            sys.stdout.write('checking out submission %d\n' % opts.id)
            # Duplicate so we don't get a detached error
            sub = Submission(sub2.team, sub2.problem, sub2.language, sub2.file, sub2.submitted, sub2.verdict, sub2.judge_response)
            sub.id = sub2.id
    else:
        db = models.get_db(j.DB_CONN_STRING)
        try:
            sess = db()
            opts.id = int(opts.id)

            sub2 = sess.query(Submission).filter_by(id=opts.id).first()
            if not sub2:
                sys.stderr.write('error: submission with id %d not found\n' % opts.id)
                exit(1)

            qsub = sess.query(SubmissionQueue).filter_by(submission_id=opts.id).first()
            if qsub:
                qsub.dequeued_at = datetime.datetime.now()
                qsub.status = 1
                sess.commit()
            # Duplicate so we don't get a detached error
            sub = Submission(sub2.team, sub2.problem, sub2.language, sub2.file, sub2.submitted, sub2.verdict, sub2.judge_response)
            sub.id = sub2.id
        finally:
            sess.close()

    lang = load(j.LANGUAGES_FILE)[sub.language]
    path = os.path.join(CWD, str(opts.id))
    if os.path.isdir(path):
        shutil.rmtree(path)

    os.mkdir(path)
    with open(os.path.join(path, 'submission.yaml'), 'w') as f:
        f.write(dump({
            'id': sub.id,
            'team': sub.team,
            'problem': sub.problem,
            'submitted': sub.submitted,
            'verdict': sub.verdict,
            'judge_response': sub.judge_response,
            'language': {
                'name': sub.language,
                'compile': lang.get('compile'),
                'execute': lang.get('execute')
            }
        }))

    with open(os.path.join(path, lang['filename']), 'w') as f:
        f.write(sub.file)

    test_dir = os.path.join(j.CONTEST_DIR, 'problems', sub.problem, '.epsilon', 'tests')
    test_dst = os.path.abspath(os.path.join(path, 'tests'))

    shutil.copytree(test_dir, test_dst,
                    ignore=lambda dir, files: [f for f in files if not (f.endswith(".in") or f.endswith(".out"))])

    # for (dirpath, dirnames, filenames) in os.walk(test_dst):
    #     for f in filenames:
    #         a = f.replace("sample", "sa").replace("secret", "sc").replace("__", "")
    #         os.rename(os.path.join(dirpath, f), os.path.join(dirpath, a))
    return str(opts.id)


def do_current_submit(opts, parser, cwd=None):
    if cwd is None:
        cwd = CWD
    subdetails = load(os.path.join(cwd, 'submission.yaml'))
    sid = int(subdetails['id'])

    db = models.get_db(j.DB_CONN_STRING)
    try:
        sess = db()
        sub = sess.query(Submission).filter_by(id=sid).first()
        if not sub:
            sys.stderr.write('error: submission with id %d not found\n' % opts.id)
            exit(1)

        qsub = sess.query(SubmissionQueue).filter_by(submission_id=sid).first()
        if opts.verdict == 'QU':
            if qsub:
                qsub.dequeued_at = None
                qsub.status = 0
            else:
                sess.add(SubmissionQueue(sid))
        else:
            if qsub:
                sess.delete(qsub)
                sess.commit()

        sub.verdict = opts.verdict
        if opts.message:
            sub.judge_response = opts.message

        if sub.verdict == 'AC':
            j.deliver_balloon(sess, sub)

        sess.commit()

    finally:
        sess.close()


def do_current_compile(opts, parser, cwd=None):
    if cwd is None:
        cwd = CWD
    subdetails = load(os.path.join(cwd, 'submission.yaml'))
    sid = int(subdetails['id'])

    db = models.get_db(j.DB_CONN_STRING)
    try:
        sess = db()
        sub = sess.query(Submission).filter_by(id=sid).first()
        if not sub:
            sys.stderr.write('error: submission with id %d not found\n' % opts.id)
            exit(1)

        lang = load(j.LANGUAGES_FILE)[sub.language]

        if 'compile' in lang:
            proc = Popen(lang['compile'], stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=cwd)
            comp_err = proc.communicate()[1]
            comp_err = '' if comp_err is None else comp_err.decode('utf-8')
            if proc.wait() != 0:
                sys.stdout.write('compile error:\n' + comp_err + '\n')
            else:
                sys.stdout.write('compile successful\n')
        else:
            sys.stdout.write('no compiler for this language\n')

    finally:
        sess.close()


def do_current_execute(opts, parser, cwd=None, data=None):
    if cwd is None:
        cwd = CWD
    subdetails = load(os.path.join(cwd, 'submission.yaml'))
    sid = int(subdetails['id'])

    db = models.get_db(j.DB_CONN_STRING)
    try:
        sess = db()
        sub = sess.query(Submission).filter_by(id=sid).first()
        if not sub:
            sys.stderr.write('error: submission with id %d not found\n' % opts.id)
            exit(1)

        lang = load(j.LANGUAGES_FILE)[sub.language]
        proc = None
        if data:
            proc = Popen(lang['execute'], stdin=PIPE, cwd=cwd)
            proc.communicate(input=data.encode())
        else:
            proc = Popen(lang['execute'], cwd=cwd)
        proc.wait()

    finally:
        sess.close()


def do_current(opts, parser):
    if opts.current_cmd_subparser_name is None:
        parser.print_help()
        exit(0)

    actions = {'submit': do_current_submit, 'compile': do_current_compile, 'execute': do_current_execute}
    actions[opts.current_cmd_subparser_name](opts, parser)


verdict_explanation = {
    'QU': 'in queue',
    'AC': 'accepted',
    'PE': 'presentation error',
    'WA': 'wrong answer',
    'CE': 'compile time error',
    'RE': 'runtime error',
    'TL': 'time limit exceeded',
    'ML': 'memory limit exceeded',
    'SE': 'submission error',
    'RF': 'restricted function',
    'CJ': 'cannot judge',
}


def do_help(opts, parser):
    if opts.item == "verdicts":
        print("\n".join("%s: %s" % (k, v) for k, v in verdict_explanation.items()))


def load_contest(name=None):
    global contest
    if name:
        contest = j.load_contest(name)
    else:
        contest = j.load_contest(os.getenv("CONTEST", name))


def main(argv):
    parser = argparse.ArgumentParser(description='A command line judge interface.')
    parser.add_argument('-c', '--contest', help='contest')

    subparsers = parser.add_subparsers(dest='subparser_name')

    list_cmd = subparsers.add_parser('list', help='list submissions')
    list_cmd.add_argument('type', help='which submissions to list')
    list_cmd.add_argument('-t', '--team', help='filter by team')
    list_cmd.add_argument('-p', '--problem', help='filter by problem')

    checkout_cmd = subparsers.add_parser('checkout', help='checkout submission')
    checkout_cmd.add_argument('id', help='which submissions to checkout')
    # checkout_cmd.add_argument('-t', '--time', default=j.SUBMISSION_JUDGE_TIMEOUT, help='how long the submission should be checked out for')

    current_cmd = subparsers.add_parser('current', help='various operations for the current submission')

    current_cmd_subparsers = current_cmd.add_subparsers(dest='current_cmd_subparser_name')
    current_cmd_submit = current_cmd_subparsers.add_parser('submit', help='submit the current submission (see help verdicts for explanations)')
    current_cmd_submit.add_argument('verdict', help='the verdict', choices=verdict_explanation.keys())
    current_cmd_submit.add_argument('-m', '--message', help='a message with the verdict')

    current_cmd_compile = current_cmd_subparsers.add_parser('compile', help='compile the current submission')
    current_cmd_execute = current_cmd_subparsers.add_parser('execute', help='execute the current submission')

    help_cmd = subparsers.add_parser('help', help="additional information for submissions")
    help_cmd.add_argument("item", help="what item to help with")

    opts = parser.parse_args(argv)
    load_contest(opts.contest)

    if opts.subparser_name is None:
        parser.print_help()
        exit(0)

    actions = {'list': do_list, 'checkout': do_checkout, 'current': do_current, 'help': do_help}
    try:
        actions[opts.subparser_name](opts, parser)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main(sys.argv[1:])
