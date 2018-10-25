
import re, io
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
    def __init__(self, fname, mode='r', config={}, **kw):
        self.parseGithubUrl(fname)
        self.mode = mode
        self.username = config.get('username', None)
        self.password = config.get('password', None)
        self.log = None
        if mode == 'w':
            super(GithubFile, self).__init__()
            return
        git = Github()
        org = git.get_user(self.user)
        repo = org.get_repo(self.repo)
        f = branch.get_file_contents(self.path, ref=self.branch)
        super(GithubFile, self).__init__(f.content)
        
    def parseGithubUrl(self, s):
        m = re.match(r'https://github.com/(?P<user>.*?)/(?P<repo>.*?)/blob/(?P<branch>.*?)/(?P<path>.*)$', s)
        if not m:
            raise IOError((0, "Can't parse github filename", s))
        self.user = m.group('user')
        self.repo = m.group('repo')
        self.branch = m.group('branch')
        self.path = m.group('path')

    def close(self):
        super(GithubFile, self).close()
        if self.mode == 'w':
            s = self.getvalue()
        if self.username is not None:
            git = Github(self.username, self.password)
        else:
            git = Github(self.password)
        if self.log is None:
            self.log = "Committed from diffted"
        repo = g.get_user(self.org).get_repo(self.repo)
        ref = repo.get_git_ref(self.branch)
        sha = ref.object.sha
        base_tree = repo.get_git_tree(sha)
        element_list = [InputGitTreeElement(self.path, '100644', 'blob', self.getval())]
        tree = repo.create_git_tree(element_list, base_tree)
        parent = repo.get_git_commit(sha)
        commit = repo.create_git_commit(self.log, tree, [parent])
        ref.edit(commit.sha)
