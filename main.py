import sublime
import sublime_plugin
import os
import re
import subprocess
import json
from copy import deepcopy

package_name = "Grunt"
package_url = "https://github.com/tvooo/sublime-grunt"

regex_json = re.compile(r'EXPOSE_BEGIN(.*)EXPOSE_END', re.M | re.I | re.DOTALL)


class GruntRunner(object):
    def __init__(self, window):
        self.window = window
        self.list_gruntfiles()

    def list_tasks(self):
        path = settings().get('exec_args').get('path')
        package_path = os.path.join(sublime.packages_path(), package_name)
        args = 'grunt --no-color --tasks "' + package_path + '" expose'

        (stdout, stderr) = subprocess.Popen(args, stdout=subprocess.PIPE, env={"PATH": path}, cwd=self.wd, shell=True).communicate()
        stdout = stdout.decode('utf8')
        json_match = regex_json.search(stdout)

        if json_match is not None:
            try:
                json_result = json.loads(json_match.groups()[0])
            except TypeError:
                self.window.run_command("grunt_error", {"message": "SublimeGrunt: JSON is malformed\n\n" + json_match.groups()[0]})
                sublime.error_message("Could not read available tasks\n")
            else:
                tasks = [[name, task['info'], task['multi'], task['targets']] for name, task in json_result.items()]
                return sorted(tasks, key=lambda task: task)
        else:
            self.window.run_command("grunt_error", {"message": "SublimeGrunt: Could not expose available tasks\n\n" + stdout})
            sublime.error_message("Could not expose available tasks\n")

    def list_gruntfiles(self):
        self.grunt_files = []
        self.folders = []
        for f in self.window.folders():
            self.folders.append(f)
            if os.path.exists(os.path.join(f, "Gruntfile.js")):
                self.grunt_files.append(os.path.join(f, "Gruntfile.js"))
            elif os.path.exists(os.path.join(f, "Gruntfile.coffee")):
                self.grunt_files.append(os.path.join(f, "Gruntfile.coffee"))
        if len(self.grunt_files) > 0:
            if len(self.grunt_files) == 1:
                self.choose_file(0)
            else:
                self.window.show_quick_panel(self.grunt_files, self.choose_file)
        else:
            sublime.error_message("Gruntfile.js or Gruntfile.coffee not found!")

    def choose_file(self, file):
        self.wd = os.path.dirname(self.grunt_files[file])
        self.tasks = self.list_tasks()
        if self.tasks is not None:
            self.window.show_quick_panel(self.format_panel_tasks(self.tasks), self.on_task_select)

    def on_task_select(self, task):
        if task > -1:
            self.selected_task = self.tasks[task];
            targets = self.selected_task[3]
            if len(targets):
                targets.append('(Run all targets)');
                sublime.set_timeout(lambda: self.window.show_quick_panel(
                    targets,
                    self.on_task_target_select
                ), 1)
            else:
                self.run_task(self.selected_task[0])

    def on_task_target_select(self, target):
        if len(self.selected_task[3])-1 == target:
            self.run_task(self.selected_task[0])
        else:
            self.run_task(self.selected_task[0] + ':' + self.selected_task[3][target])

    def run_task(self, task_name):
        exec_args = settings().get('exec_args')
        exec_args.update({'cmd': u"grunt --no-color " + task_name, 'shell': True, 'working_dir': self.wd})
        self.window.run_command("exec", exec_args)

    def format_panel_tasks(self, tasks):
        formatted_tasks = deepcopy(tasks)
        for i, task in enumerate(formatted_tasks):
            formatted_tasks[i][3] = 'Targets: ' + (', '.join(task[3]) if task[2] == True and len(task[3]) else 'None')
            del formatted_tasks[i][2]
        return formatted_tasks


def settings():
    return sublime.load_settings('SublimeGrunt.sublime-settings')


class GruntCommand(sublime_plugin.WindowCommand):
    def run(self):
        GruntRunner(self.window)


class GruntKillCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command("exec", {"kill": True})

class GruntErrorCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        view = self.view
        prefix = "Please file an issue on " + package_url + "/issues and attach this output.\n\n"
        view.insert(edit, 0, prefix + args["message"])
