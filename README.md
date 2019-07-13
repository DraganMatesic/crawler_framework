# Crawler Framework
#### About
Main objective is to secure fast deployment of crawler system that will help you setup all that you need to 
get started with data mining interactively over cmd/terminal.
Concept is based on long working experience and mistakes that have been learned over the years in data mining 
and database arhitecture. It could save you a lot of time and effort using this framework.
Currently works on Win OS.

### Installation
Most important thing is that you have python 3 installed on your machine. 

**With virtual environment (recommended)**<br>
First install virtual environment ```pip3.7 install virtualenvwrapper-win``` <br>
Then create virtual environment ```mkvirtualenv myvenv``` <br>
By default now your virtual environment should be active if it isn't activate your virtual 
environment by writing ```workon myvenv```  <br>
Now you can install library  ```pip install crawler_framework```

**Without virtual environment**<br>
Just open cmd and write ```pip3.7 install crawler_framework```. This option is ok if you have only one version 
of python installed on your system. But if you have more python version installed and you decide to go with this 
option you will have to finish some additional question's during configuration of crawler framework. 
Like that it will be ensured that everything works ether way.

### Setup
#### Database configuration
Before we can deploy anything we must setup connection strings for one or more database 
servers that we are going to use.
Currently supported are PostgreSQL, Oracle and Microsoft SQL Server.


**Step 1**

Open cmd/terminal and write dbconfig.py. If everything goes well you should see this options below. 
It is possible that program asks for some additional information if you have more than one python interpreter 
installed on your machine and you did not use virtual environment. But it will be required only once.

![dbconfig](https://raw.githubusercontent.com/DraganMatesic/crawler_framework/master/images/dbconfig.PNG)

**Step 2**

Create all database connection's that you think you will use, from database where you will deploy crawler_framework 
to database where you will store data etc. by entering number 1.



