# Memorandum
This is simple multiuser web file manager, which was created using Django python framework.
Memorandum makes user home directory accessible from the Internet and allows to edit, rename,
delete and upload files or directories. It also provides an opportunity to share your home
directory with another user and define his permissions. Here are some screenshots:

![Folder view](/doc/screenshots/folder.png)
![Code Editor](/doc/screenshots/code_editor.png)
![PDF viewer](/doc/screenshots/pdf_viewer.png)

# Installation
To run Memorandum on your PC, you need python 3.x and django 1.10.

 - Install python 3 and django if you don't have them already installed.
 - Clone this repository: `git clone https://github.com/bshishov/Memorandum`
 - Go to cloned folder `cd Memorandum`
 - Install python requirements `pip install -r requirements.txt`
 - Create file `local_settings.py` containing settings specific for your local machine in `memorandum` folder, take a look at `memorandum/local_settings.py.sample` for reference.
 - Initialize a database by appliing migrations `python manage.py migrate`
 - Create a first superuser for the application by running `python manage.py createsuperuser`. You will be asked for some information required to run the server.
 - Run the website `python manage.py runserver 0.0.0.0:8000`.
 - In the browser go to `http://localhost:8000/` and login using your creditentials.

# Concept
Memorandum is a web file manager so it manages files and directories on your hard drive. Hovewer, we were used to implement an abstraction level on top of OS files, directories in operations on them, here are main concepts:

## Item
Item - is an abstraction of a real file or a directory represented by `items.Item` class. It contains methods like `rename`, `delete` and properties like `absolute_path`, `name`, `created` to work with it. There are two child classes:
 - Directory Item (`items.DirectoryItem`) which implements some specific for directories methods and properties like child items management.
 - File Item (`items.FileItem`) which implements some specific for files methods and properties like file content.
The whole item abstraction doesn't refer to web features and http itself. It is just a pure python OOP abstraction on files and directories.

## Editor
Editor - is an object used to perfom actions on specified items. It is represented by a class (`editors.Editor`) with a methods which handles an item as as input and returns Http response as an output. Each editor also has a `can_handle` method which decides whether the editor can handle the passed item or not. If it does than an action could be called.

There are some basic editors like DirectoryEditor which handles only DirectoryItem and just lists child items in the template. And a FileEditor with common file operations like `rename`,`download` required for a web file server.

### Action
Action - is an operation that could be performed on an item. It is implemented as an editors' methods. Default action is `view` so if no other action passed the editor should call view method of itself and return a httpresponse as a result.


# Structure
 * `doc` - contains various documentation, including screenshots.
 * `main` - main django application for Memorandum project.
 * `memoramdum` - Memorandum django project directory.
