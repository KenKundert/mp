import os, errno
from fnmatch import fnmatch

"""Various utilities for interacting with files and directories."""

# Globbing Utilities {{{1
def getAll(pattern='*'):
    """
    Get all items that match a particular glob pattern.
    Supports *, ? and [] globbing (including [!]), but does not support {}
    """
    import glob
    pattern = os.path.expanduser(pattern)
    pattern = os.path.expandvars(pattern)
    return glob.glob(pattern)

def getFiles(pattern='*'):
    """
    Get all files that match a particular glob pattern.
    """
    return [each for each in getAll(pattern) if os.path.isfile(each)]

def getDirs(pattern='*'):
    """
    Get all directories that match a particular glob pattern.
    """
    return [each for each in getAll(pattern) if os.path.isdir(each)]

def getFilesRecursively(path, acceptCriteria = None, rejectCriteria = None, exclude = None):
    """
    Returns a generator that iterates through all the files contained in a
    directory hierarchy.  Accept and reject criteria are glob strings, or lists
    of glob strings. For a file to be returned its name must not match any of
    the reject criteria if any are given, and it must match one of the accept
    criteria, if any are given.  If no criteria are given, all files are
    returned. Exclude is a file or directory or a list of files or directories
    to exclude. Each is specified relative from the current working directory.
    """
    if type(acceptCriteria) == str:
        acceptCriteria = [acceptCriteria]
    if type(rejectCriteria) == str:
        rejectCriteria = [rejectCriteria]
    def yieldFile(filename):
        filename = getTail(filename)
        if acceptCriteria != None:
            if rejectCriteria != None:
                for criterion in rejectCriteria:
                    if fnmatch(filename, criterion):
                        return False
            for criterion in acceptCriteria:
                if fnmatch(filename, criterion):
                    return True
            return False
        else:
            if rejectCriteria != None:
                for criterion in rejectCriteria:
                    if fnmatch(filename, criterion):
                        return False
            return True

    def prepExcludes(exclude):
        if not exclude:
            return []
        if type(exclude) == str:
            exclude = [exclude]
        excludes = []
        for each in exclude:
            excludes += [splitPath(each)]
        return excludes

    def skip(path, excludes):
        for each in excludes:
            if splitPath(path)[0:len(each)] == each:
                return True
        return False

    if isFile(path):
        if yieldFile(path):
            yield path
    else:
        excludes = prepExcludes(exclude)
        for path, subdirs, files in os.walk(path):
            for file in files:
                filename = makePath(path, file)
                if skip(filename, excludes):
                    continue
                if yieldFile(filename):
                    yield filename

# Type Utilities {{{1
def isFile(path):
    """
    Determine whether path corresponds to a file.
    """
    return os.path.isfile(path)

def isDir(path):
    """
    Determine whether path corresponds to a directory.
    """
    return os.path.isdir(path)

def isLink(path):
    """
    Determine whether path corresponds to a symbolic link.
    """
    return os.path.islink(path)

def exists(path):
    """
    Determine whether path corresponds to a file or directory.
    """
    return os.path.exists(path)

# File Type Utilities {{{2
def fileIsReadable(filepath):
    """
    Determine whether file exists and is readable by user.
    """
    return os.path.isfile(filepath) and os.access(filepath, os.R_OK)

def fileIsExecutable(filepath):
    """
    Determine whether file exists and is executable by user.
    """
    return os.path.isfile(filepath) and os.access(filepath, os.X_OK)

def fileIsWritable(filepath):
    """
    If filepath exists, determine whether it is writable by user.
    If not, determine if directory is writable by user.
    """
    if os.path.isfile(filepath) and os.access(filepath, os.W_OK):
        return True
    else:
        path = os.path.split(filepath)
        dirpath = os.path.join(*path[:-1])
        return os.path.isdir(dirpath) and os.access(filepath, os.W_OK)

# Directory Utilities {{{2
def dirIsReadable(dirpath):
    """
    Determine whether directory exists and is readable by user.
    """
    return os.path.isdir(dirpath) and os.access(dirpath, os.R_OK)

def dirIsWritable(dirpath):
    """
    Determine whether directory exists and is executable by user.
    """
    return os.path.isdir(dirpath) and os.access(dirpath, os.W_OK)


# Path Utilities {{{1
# Joins arguments into a filesystem path
def makePath(*args):
    """
    Join the arguments together into a filesystem path.
    """
    return os.path.join(*args)

# Splits path at directory boundaries into its component pieces
def splitPath(path):
    """
    Split the path at directory boundaries.
    """
    return path.split(os.path.sep)

# Return normalized path
def normPath(path):
    """
    Convert to a normalized path (remove redundant separators and up-level references).
    """
    return os.path.normpath(path)

# Return absolute path
def absPath(path):
    """
    Convert to an absolute path.
    """
    return os.path.abspath(normPath(path))

# Return relative path
def relPath(path, start = None):
    """
    Convert to an relative path.
    """
    if start:
        return os.path.relpath(normPath(path), start)
    else:
        return os.path.relpath(normPath(path))

# Perform common path expansions (user, envvars)
def expandPath(path):
    """
    Expand initial ~ and any variables in a path.
    """
    path = os.path.expandvars(path)
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    return path

# Access components of a path {{{2
# Head (dir/file.ext ==> dir)
def getHead(path):
    """
    Return head of path: dir/file.ext ==> dir
    """
    return os.path.split(path)[0]

# Tail (dir/file.ext ==> file.ext)
def getTail(path):
    """
    Return tail of path: dir/file.ext ==> file.ext
    """
    return os.path.split(path)[1]

# Root (dir/file.ext ==> dir/file)
def getRoot(path):
    """
    Return root of path: dir/file.ext ==> dir/file
    """
    return os.path.splitext(path)[0]

# Extension (dir/file.ext ==> ext)
def getExt(path):
    """
    Return root of path: dir/file.ext ==> ext
    """
    ext = os.path.splitext(path)[1]
    return ext[1:] if ext else ''

# Copy, Move, Remove Utilities {{{1
def copy(src, dest):
    """
    Copy either a file or a directory.
    """
    import shutil
    destpath = splitPath(dest)[0:-1]
    if destpath:
        destpath = makePath(*destpath)
        if not exists(destpath):
            os.makedirs(destpath)
    try:
        if isDir(src):
            shutil.copytree(src, dest, symlinks=True)
        else:
            shutil.copy2(src, dest)
    except (IOError, OSError) as err:
        exit("%s: %s." % (err.filename, err.strerror))
    except shutil.Error as err:
        exit(["%s to %s: %s." % arg for arg in err.args])

def move(src, dest):
    """
    Move either a file or a directory.
    """
    import shutil
    try:
        shutil.move(src, dest)
    except (IOError, OSError) as err:
        exit("%s: %s." % (err.filename, err.strerror))
    except shutil.Error as err:
        exit("Cannot rename %s to %s: %s." % (src, dest, ', '.join(err.args)))

def remove(path, exitUponError=True):
    """
    Remove either a file or a directory.
    """
    # if exists(path): # do not test for existence, this will causes misdirected symlinks to be ignored
    try:
        if isDir(path):
            import shutil
            shutil.rmtree(path)
        else:
            os.remove(path)
    except (IOError, OSError) as err:
        # don't complain if the file never existed
        if err.errno != errno.ENOENT:
            if exitUponError:
                exit("%s: %s." % (err.filename, err.strerror))
            else:
                raise

def makeLink(src, dest):
    """
    Create a symbolic link.
    """
    try:
        os.symlink(src, dest)
    except (IOError, OSError) as err:
        exit("%s: %s." % (dest, err.strerror))

def mkdir(path):
    """
    Create a directory if it does not exist. If it does, return without complaint.
    """
    try:
        os.makedirs(path)
    except (IOError, OSError) as err:
        if err.errno != errno.EEXIST:
            exit("%s: %s." % (err.filename, err.strerror))

# Execute Utilities {{{1
class ExecuteError(Exception):
    def __init__(self, cmd, error, filename=None, showCmd=False):
        self.cmd = cmd if type(cmd) is str else ' '.join(cmd)
        self.filename = filename
        self.error = error
        self.showCmd = showCmd

    def __str__(self):
        if self.showCmd:
            cmd = (
                self.filename
                if self.filename
                else (
                    self.cmd if self.showCmd == 'full' else self.cmd.split()[0]
                )
            )
            return "%s: %s" % (cmd, self.error)
        else:
            return "%s" % self.error

class Execute():
    def __init__(
        self, cmd, accept=(0,), stdin=None, stdout=True, stderr=True, wait=True, 
        shell=False, showCmd=False
    ):
        """
        Execute a command and capture its output

        Raise an ExecuteError if return status is not in accept unless accept
        is set to True. By default, only a status of 0 is accepted.

        If stdin is None, no connection is made to the standard input, otherwise 
        stdin is expected to be a string and that string is sent to stdin.

        If stdout / stderr is true, stdout / stderr is captured and made 
        avilable from self.stdout / self.stderr.

        If wait is true, the run method does not return until the process ends.  
        In this case run() does not return the status. Instead, calling wait() 
        return the status.

        Once the process is finished, the status is also available from 
        self.status,

        The default is to not use a shell to execute a command (safer).
        """
        self.cmd = cmd
        self.accept = accept
        self.save_stdout = stdout
        self.save_stderr = stderr
        self.wait_for_termination = wait
        self.showCmd = showCmd
        self._run(stdin, shell)

    def _run(self, stdin, shell):
        import subprocess
        streams = {}
        if stdin is not None:
            streams['stdin'] = subprocess.PIPE
        if self.save_stdout:
            streams['stdout'] = subprocess.PIPE
        if self.save_stderr:
            streams['stderr'] = subprocess.PIPE
        try:
            process = subprocess.Popen(
                self.cmd, shell=shell, **streams
            )
        except (IOError, OSError) as err:
            raise ExecuteError(self.cmd, err.filename, err.strerror)
        if stdin is not None:
            process.stdin.write(stdin.encode('utf-8'))
            process.stdin.close()
        self.pid = process.pid
        self.process = process
        if self.wait_for_termination:
            return self.wait()

    def wait(self):
        if self.save_stdout:
            self.stdout = self.process.stdout.read().decode('utf-8')
        else:
             self.stderr = None
        if self.save_stderr:
            self.stderr = self.process.stderr.read().decode('utf-8')
        else:
             self.stderr = None
        self.status = self.process.wait()
        self.process.stdout.close()
        self.process.stderr.close()
        if self.accept is not True and self.status not in self.accept:
            if self.stderr:
                raise ExecuteError(self.cmd, self.stderr, showCmd=self.showCmd)
            else:
                raise ExecuteError(
                    self.cmd,
                    "unexpected exit status (%d)." % self.status,
                    showCmd=self.showCmd)
        return self.status


class ShellExecute(Execute):
    def __init__(
        self, cmd, accept=(0,), stdin=None, stdout=True, stderr=True, wait=True, 
        shell=True, showCmd=False
    ):
        """
        Execute a command in a shell and capture its output

        This class is the same as Execute, except that by default it runs the 
        given command in a shell, which is less safe but more convenient.
        """
        self.cmd = cmd
        self.accept = accept
        self.save_stdout = stdout
        self.save_stderr = stderr
        self.wait_for_termination = wait
        self.showCmd = showCmd
        self._run(stdin, True)


def execute(cmd, accept=(0,), stdin=None, shell=False):
    """
    Execute a command without capturing its output

    Raise an ExecuteError if return status is not in accept unless accept
    is set to True. By default, only a status of 0 is accepted. The default is 
    to not use a shell to execute a command (safer).
    If stdin is None, no connection is made to the standard input, otherwise 
    stdin is expected to be a string.
    """
    import subprocess
    streams = {'stdin': subprocess.PIPE} if stdin is not None else {}
    try:
        process = subprocess.Popen(cmd, shell=shell, **streams)
    except (IOError, OSError) as err:
        raise ExecuteError(cmd, err.filename, err.strerror)
    if stdin is not None:
        process.stdin.write(stdin.encode('utf-8'))
        process.stdin.close()
    status = process.wait()
    if accept is not True and status not in accept:
        raise ExecuteError(
            cmd,
            "unexpected exit status (%d)." % status,
            showCmd='brief'
        )
    return status

def shellExecute(cmd, accept=(0,), stdin=None, shell=True):
    """
    Execute a command without capturing its output

    Raise an ExecuteError if return status is not in accept unless accept
    is set to True. By default, only a status of 0 is accepted. The default is 
    to use a shell to execute a command (more convenient).
    """
    return execute(cmd, accept, stdin, shell=True)


def background(cmd, stdin=None, shell=False):
    """
    Execute a command in the background without capturing its output.

    If stdin is None, no connection is made to the standard input, otherwise 
    stdin is expected to be a string.
    """
    import subprocess
    streams = {'stdin': subprocess.PIPE} if stdin is not None else {}
    try:
        process = subprocess.Popen(cmd, shell=shell, **streams)
    except (IOError, OSError) as err:
        raise ExecuteError(cmd, err.filename, err.strerror)
    if stdin is not None:
        process.stdin.write(stdin.encode('utf-8'))
        process.stdin.close()
    return process.pid

def shellBackground(cmd, stdin=None, shell=True):
    """
    Execute a command in the background without capturing its output.

    If stdin is None, no connection is made to the standard input, otherwise 
    stdin is expected to be a string.

    The default is to use a shell to execute a command (more convenient).
    """
    return execute(cmd, stdin, shell=True)


def which(name, flags=os.X_OK):
    """Search PATH for executable files with the given name.

    Arguments:
    name (str): The name for which to search.
    flags (int): Arguments to os.access.

    A list of the full paths to files found, in the order in which they were
    found.
    """
    result = []
    path = os.environ.get('PATH', '')
    for p in path.split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
    return result

# vim: set sw=4 sts=4 et:
