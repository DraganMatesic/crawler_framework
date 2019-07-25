# About
Main objective is to secure fast deployment of crawler system that will help you setup all that you need to 
get started with data mining interactively over cmd/terminal.
Concept is based on long working experience and mistakes that have been learned over the years in data mining 
and database arhitecture. It could save you a lot of time and effort using this framework.
Currently works on Win OS.

# Installation
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

# Setup
## Database configuration
Before we can deploy anything we must setup connection strings for one or more database 
servers that we are going to use.
Currently supported are PostgreSQL, Oracle and Microsoft SQL Server.

<i>It is recommended to create database on your server that will only be used by framework. </i>


Open cmd/terminal and write  ```config.py```. If everything goes well you should see this options below. 
It is possible that program asks for some additional information if you have more than one python interpreter 
installed on your machine and you did not use virtual environment. But it will be required only once.

![dbconfig](https://raw.githubusercontent.com/DraganMatesic/crawler_framework/master/images/config.PNG)

Create all database connection's that you think you will use, from database where you will deploy crawler_framework 
to database where you will store data etc. by selecting option number 1 and then database option number one.

![dbconfig](https://raw.githubusercontent.com/DraganMatesic/crawler_framework/master/images/dbconfig.PNG)

### Hints
**Microsoft SQL Server** <br>
 If you are using default option be sure to define in ODBC Data sources administrator dsn name that will have 
 default database that will be used for framework. If you are using pymssql you will define server_ip, port and database 
 during database configuration stage.
 
## Deploying framework
Open cmd/terminal and write  ```config.py```. Select option 2 (Deploy framework) and then select option from 
the list of connections you created that is going to be used for deployment. This will deploy table structure in selected database 
on selected server connection. In our case we will deploy it on PostgreSQL localhost server.

## Starting proxy server
Proxy server is multifunctional program that acquires new proxies(crawlers), test proxies, creates tor network etc.
 
 


