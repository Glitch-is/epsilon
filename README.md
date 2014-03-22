
epsilon
=======

A minimal programming contest environment, specifically created for [Iceland's
High School Programming Contest](http://forritun.is).

It consists of four components:
- A postgresql database. All submissions are stored here.
- A programming contest server. Serves a web page where contestants can submit
  solutions and view a scoreboard. Also hosts a small interface for judges.
- An automatic judge. Automatically judges solutions in various programming
  languages.
- A manual judge. A command line tool for manually judging solutions.

Status of the project
---------------------

The programming contest environment was specifically created for Iceland's High
School Programming Contest held in March, 2014. The contest was a great
success, and epsilon served its purpose well. There are no plans to develop the
project any further, unless maybe for next year's contest. If you are planning
to hold your own contest, epsilon, being specifically designed for this one
contest, may or may not fit your needs (probably not though). I recommend
taking a look at better developed programming contest environments such as
[DOMJudge](http://www.domjudge.org/).

Installing
----------

Start by setting up postgresql on your server.

There are a number of prerequisites that need to be installed, such as
programming languages and [jailkit](http://olivier.sessink.nl/jailkit/). Two
setup scripts are provided for installing all these things, one for Arch Linux
and one for Ubuntu.

For Arch Linux:

    cd scripts/arch
    ./setup-all-quick.sh

For Ubuntu:

    cd scripts/ubuntu
    ./setup-all.sh

Note that the Arch Linux script is much faster and simpler, since it installs
packages with `pacman`, instead of manually building the packages, which the
Ubuntu script does. This is to provide more up-to-date versions of the
languages for Ubuntu, but can probably also be done through `apt-get`.

After installing all prerequisites, the programming contest environment can be
installed by doing:

    sudo ./setup.py install

This installs files into the default prefix, which is `/opt/epsilon`, but this
can be changed with parameters to the setup script. Take note of the last piece
of output generated by the setup script. It asks you to append a line to the
`/etc/sudoers` file. Go ahead and do so.

The programming contest environment should now be installed.

Hosting a contest
-----------------

The most important part of hosting the contest is to prepare the problems and
contest configuration. Take a look inside the `example_contests` directory for
examples.

Create a postgresql database along with a user with full access to that
database (there are some helper scripts in `server/db`). Make sure that the
`db` and `db_conn_string` properties in `config.yml` and `judge.yml` are set
appropriately.

Now start the programming contest server by executing (optionally change the
path to your contest directory):

    epsilon-server -p 8080 example_contests/fk_2013_beta

This creates the appropriate database tables if they don't exist, and then
starts an HTTP server on port 8080. Navigate to `http://localhost:8080` and you
should see the web interface.

### Automatic judging

Multiple automatic judge processes can be spawned as follows:

    epsilon-judge example_contests/fk_2013_beta/judge.yml 1
    epsilon-judge example_contests/fk_2013_beta/judge.yml 2

The automatic judge executes submissions inside a `chroot` jail, and uses
[Mooshak's](https://mooshak.dcc.fc.up.pt/) `safeexec` program to limit CPU
time, memory usage, forking, and other things. The jail has **not** been
extensively tested, and currently there are some design flaws. The jail also
does not prevent network traffic.

### Manual judging

Start by creating the following alias to simplify later usage.

    alias judge="epsilon-manual-judge -c $(realpath example_contests/fk_2013_beta/judge.yml)"

We will now use the `judge` command to judge submissions. Several commands are
supported. For example:

- List all submissions.

    `judge list all`

- List submissions that have not been judged yet, excluding submissions already
  checked out by other judges.

    `judge list queue`

- Check out the submission with the given ID for judging. This will create a
  directory whose name is the same as the ID of the submission. The directory
  contains the solution code (usually in a file named sol.ext), a yaml file
  containing information about the submission (don't change it unless you know
  what you're doing), and a directory containing test cases for the
  corresponding problem.

    `judge checkout ID`

- Check out the next unjudged submission, waiting for it if necessary.

    `judge checkout next`

- When inside a submission directory, the following commands are available:
    - Compile the solution.

        `judge current compile`

    - Execute the solution.

        `judge current execute`

    - Submit the judgment verdict to the database. Verdict can be one of AC
      (Accepted), WA (Wrong Answer), RE (Runtime Error), CE (Compile Error), ML
      (Memory Limit Exceeded), TL (Time Limit Exceeded), and other less
      commonly used verdicts. An optional HTML message to the contestant can be
      attached by setting the -m option followed by the message.

        `judge current submit VERDICT`

One can make a temporary judging directory in `/tmp`. Then a small judging
session might look like the following:

    mkdir /tmp/judging
    cd /tmp/judging
    judge list queue
    judge checkout 23
    cd 23
    cat submission.yml
    cat sol.cs
    judge current compile
    judge current execute < tests/00.in
    judge current execute < tests/01.in | diff - tests/01.out
    judge current submit WA
    cd ..
    judge checkout next
    cd 25
    cat sol.cpp
    judge current compile
    judge submit CE
    cd ..
    cd ~
    rm -rf /tmp/judging


### Web judge interface

The web judge interface can be accessed by navigating to
`http://localhost:8080/judge`. Judge logins can be configured in
`example_contests/fk_2013_beta/judges.yml`.  From there you can go to the
Submissions page. By clicking on the ID of a submission, you will be taken to a
page where you can view the associated solution and submit a verdict
(optionally with an HTML message for the contestant).


### ICPC Resolver

The web judge interface can export the contest and submissions into an XML file
understood by the [ICPC Resolver](https://github.com/icpc-live/graphics).
It's an awesome animated scoreboard for incrementally resolving the "frozen"
part of the contest. We did this in our contest and the contestants had a great
time watching it! Highly recommend it...


### Using multiple judge servers

All components of the programming contest environment depend on the postgresql
server, but are otherwise completely independent. Therefore the server process
and automatic judge processes can all be distributed over many servers, with
the only requirement that they are able to contact the postgresql server.


