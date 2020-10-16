import os
import sys
import pickle
import getpass
import virtualenv
from subprocess import Popen, PIPE, call

framework_folder = r'C:\Users\{}\Documents\crawler_framework'.format(getpass.getuser())
database_log_folder = r'{}\logs'.format(framework_folder)
python_path = r'{}\py_config.pkl'.format(framework_folder)


if os.path.exists(framework_folder) is False:
    os.mkdir(framework_folder)
if os.path.exists(database_log_folder) is False:
    os.mkdir(database_log_folder)

p = Popen('py -c "import sys; import os; sys.stdout.write(sys.executable)" ', stdout=PIPE)
lines = p.stdout.readlines()
real_executable = lines[0]

p = Popen('py -c "import sys; import os; sys.stdout.write(sys.prefix)" ', stdout=PIPE)
lines = p.stdout.readlines()
lib_path = lines[0]


def is_venv():
    if sys.version_info.major < 3:
        return real_executable != sys.executable
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


def version_control():
    py_versions = {}
    sys.stdout.write('\nSelect Python3 global version to use or specifiy path to virtualenv\n')
    pythons = virtualenv.get_installed_pythons()
    for k, v in pythons.items():
        if k.startswith('3.') and not k.__contains__('-'):
            py_versions.update({len(py_versions): k})

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


if is_venv():
    print("location of venv ", lib_path)
    py_data = {'version': "venv"}
    sys.stdout.write('\nChecking paths for this Python please wait..\n')
    p = Popen('py -c "import sys; import os; sys.stdout.write(os.path.dirname(sys.executable))"',stdout=PIPE)
    lines = p.stdout.readlines()
    main_path = lines[0]

    if type(lib_path) == bytes:
        lib_path = lib_path.decode()

    workon = lib_path.rsplit("\\", 1)[1]

    if sys.version_info.major < 3:
        pycon_path = os.path.join(main_path,  'config.py')
    else:
        pycon_path = os.path.join(main_path.decode(), 'config.py')

    if os.path.exists(pycon_path) is False:
        sys.stdout.write("\n Can't locate config.py at {0} \n make sure you are using python "
                         "version where you installed this package then try again...".format(pycon_path))
        exit()
    check_path = os.path.exists(python_path)
    vent_activate = os.path.join(lib_path, 'Scripts', 'activate.bat')

    if check_path is False:
        if sys.version_info.major < 3:
            command = '"{0}"&&"{2}" "{1}"'.format(vent_activate, pycon_path, real_executable)
        else:
            command = '"{0}"&&"{2}" "{1}"'.format(vent_activate, pycon_path, real_executable)
        py_data.update({'cmd': command})
        with open(python_path, 'wb') as fw:
            pickle.dump(py_data, fw)
        print(command)
        call(command)
    else:
        if sys.version_info.major < 3:
            version_call()
        else:
            print("configurating folders")
            if type(real_executable) is bytes:
                real_executable = real_executable.decode()
            call('"{}" -c "from Scripts.configv3 import Configuration; Configuration(venv=True)"'.format(real_executable))
            # from Scripts.configv3 import Configuration
            # Configuration()
        exit()

elif sys.version_info.major < 3:
    check_path = os.path.exists(python_path)
    version = None
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
    print("Running outside virtual environment be sure to install crawler_framework for ", sys.executable)
    try:
        from Scripts.configv3 import Configuration
        Configuration()
    except ModuleNotFoundError as e:
        # conflict between python 3.x versions select default
        print(str(e))
        check_path = os.path.exists(python_path)
        if check_path is False:
            sys.stdout.write('Python 3.x multiply version detected choose one where you installed crawler_framework')
            version_control()
        else:
            version_call()
