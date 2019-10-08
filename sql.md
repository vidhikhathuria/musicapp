SQL Query to create table for storing user information:

create table users (id int(11) auto_increment primary key, name varchar(100), email varchar(100), username varchar(30),password varchar(100), register_date timestamp default current_timestamp);

SQL Query to create table to store songs added by user:

create table songs (id int(11) auto_increment primary key, song varchar(255), username varchar(100), create_date timestamp default current_timestamp);

In case you decide to change the schema of your database tables, you will have to change insert and delete queries in 'app.py' accordingly.
