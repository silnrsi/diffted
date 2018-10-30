
import re, io, base64
from github import Github, InputGitTreeElement

def openFile(fname, *a, **kw):
    if fname.startswith("https://github.com/"):
        return GithubFile(fname, *a, **kw)
    else:
        return OSFile(fname, *a, **kw)


class OSFile(io.TextIOWrapper):
    def __init__(self, fname, mode='r', config={}, **kw):
        super(OSFile, self).__init__(io.FileIO(fname, mode))
        self.path = fname


class GithubFile(io.StringIO):
    def __init__(self, fname, mode='r', **kw):
        if 'encoding' in kw:
            del kw['encoding']
        for k, v in kw.items():
            setattr(self, k, v)
        self.parseGithubUrl(fname)
        self.mode = mode
        self.log = None
        if mode == 'w':
            super(GithubFile, self).__init__()
            return
        git = self.getGithub(noui=True)
        if git is None:
            git = Github()
        if 'gui' in kw:
            kw['gui'].busyStart()
        org = git.get_user(self.user)
        repo = org.get_repo(self.repo)
        f = repo.get_file_contents(self.path, ref=self.branch)
        s = base64.b64decode(f.content).decode('utf-8')
        super(GithubFile, self).__init__(s)
        if 'gui' in kw:
            kw['gui'].busyStop()

    def getGithub(self, noui=False):
        if hasattr(self, 'gui'):
            cred = self.gui.getGithubCredentials(r'https://github.com/{}/{}'.format(self.user, self.repo), noui=noui)
            if cred is not None:
                self.username = cred['username']
                self.password = cred['pwd']
                self.log = cred.get('log', None)
        if getattr(self, 'password', None) is not None and len(self.password):
            return Github(self.username, self.password)
        elif getattr(self, 'username', None) is not None and len(self.username):
            return Github(self.username)
        else:
            return None

    def parseGithubUrl(self, s):
        m = re.match(r'https://github.com/(?P<user>.*?)/(?P<repo>.*?)/blob/(?P<branch>.*?)/(?P<path>.*)$', s)
        if not m:
            raise IOError((0, "Can't parse github filename", s))
        self.user = m.group('user')
        self.repo = m.group('repo')
        self.branch = m.group('branch')
        self.path = m.group('path')

    def close(self):
        s = self.getvalue()
        super(GithubFile, self).close()
        if self.mode != 'w':
            return
        g = self.getGithub(noui=False)
        if g is None:
            return
        if hasattr(self, 'gui'):
            self.gui.busyStart()
        if self.log is None:
            self.log = "Committed from diffted"
        repo = g.get_user(self.user).get_repo(self.repo)
        ref = repo.get_git_ref('heads/'+self.branch)
        sha = ref.object.sha
        base_tree = repo.get_git_tree(sha)
        element_list = [InputGitTreeElement(self.path, '100644', 'blob', s)]
        tree = repo.create_git_tree(element_list, base_tree)
        parent = repo.get_git_commit(sha)
        commit = repo.create_git_commit(self.log, tree, [parent])
        ref.edit(commit.sha)
        if hasattr(self, 'gui'):
            self.gui.busyStop()
