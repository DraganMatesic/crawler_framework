import os
import sys
import pickle
import getpass
from subprocess import Popen, PIPE, call

framework_folder= r'C:\Users\{}\Documents\crawler_framework'.format(getpass.getuser())
python_path = r'{}\py_config.pkl'.format(framework_folder)


def version_control():
    py_versions = {}
    sys.stdout.write('\nSelect Python3 version to use\n')
    p = Popen(['py', '--list'], stdout=PIPE)
    while True:
        line = p.stdout.readline()
        if not line:
            break
        if sys.version_info.major < 3:
            line = line.strip().strip('-')
        else:
            line = line.strip().strip(b'-').decode()
        if line.startswith('3'):
            line = line[:line.find('-')]
            py_versions.update({len(py_versions): line})
    if not py_versions:
        sys.stdout.write('\nInstall Python 3 to be able to use this framework')
        exit()

    while True:
        options = ""
        for k, v in py_versions.items():
            options += "[%s] %s\n" % (k, v)
        sys.stdout.write(options)
        if sys.version_info.major < 3:
            answer = raw_input()
        else:
            answer = input()

        if answer.isdigit() is False:
            sys.stdout.write("\n Option must be numeric value. Please try again...\n")
            continue

        selected_option = int(answer)
        if selected_option not in py_versions.keys():
            sys.stdout.write("\n Option you entered does not exist. Please try again...\n")
            continue

        py_version = py_versions.get(selected_option)
        if py_version is not None:
            py_data = {'version': py_version}
            sys.stdout.write('\nSelected Python version is %s\n' % py_version)

            sys.stdout.write('\nChecking paths for this Python pleas wait..\n')
            p = Popen(
                'py -%s -c "import sys; import os; sys.stdout.write(os.path.dirname(sys.executable))" ' % py_version,
                stdout=PIPE)
            lines = p.stdout.readlines()
            main_path = lines[0]

            if sys.version_info.major < 3:
                pycon_path = os.path.join(main_path, 'Scripts', 'config.py')
            else:
                pycon_path = os.path.join(main_path.decode(), 'Scripts', 'config.py')

            if os.path.exists(pycon_path) is False:
                sys.stdout.write("\n Can't locate config.py at {0} \n make sure you are using python "
                                 "version where you installed this package then try again...".format(pycon_path))
                exit()
            sys.stdout.write('\nPath find at %s \n'% pycon_path)

            command = 'py -{0} {1}'.format(py_version, pycon_path)
            py_data.update({'cmd': command})
            with open(python_path, 'wb') as fw:
                pickle.dump(py_data, fw)
            call(command)
        break


def version_call():
    with open(python_path, 'rb') as fr:
        data = pickle.load(fr)
        version = data.get('version')
        sys.stdout.write('\nPython version is defined in %s\n' % python_path)
        sys.stdout.write('\nSelected Python version is %s\n' % version)
        cmd = data.get('cmd')
        call(cmd)


if sys.version_info.major < 3:
    check_path = os.path.exists(python_path)
    if check_path is False:
        while True:
            sys.stdout.write('Python 2.x is not supported do you have Python 3.x? [y/n]')
            answer = raw_input()
            sys.stdout.write("\r")
            if answer.lower() not in ['y', 'n', 'yes', 'no']:
                sys.stdout.write("Answer can be y or n. Try again..\n")
                continue
            break

        if answer.lower() in ['y', 'yes']:
            version_control()
        else:
            sys.stdout.write('\nInstall Python 3 to be able to use this framework')
    else:
        version_call()
else:
    try:
        from Scripts.configv3 import *
        Configuration()
    except ModuleNotFoundError:
        # conflict between python 3.x versions select default
        check_path = os.path.exists(python_path)
        if check_path is False:
            sys.stdout.write('Python 3.x multiply version detected choose one where you installed crawler_framework')
            version_control()
        else:
            version_call()
