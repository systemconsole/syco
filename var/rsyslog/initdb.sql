CREATE DATABASE IF NOT EXISTS Syslog;
USE Syslog;
CREATE TABLE IF NOT EXISTS SystemEvents
(
        ID int unsigned not null auto_increment primary key,
        CustomerID bigint,
        ReceivedAt datetime NULL,
        DeviceReportedTime datetime NULL,
        Facility smallint NULL,
        Priority smallint NULL,
        FromHost varchar(60) NULL,
        Message text,
        NTSeverity int NULL,
        Importance int NULL,
        EventSource varchar(60),
        EventUser varchar(60) NULL,
        EventCategory int NULL,
        EventID int NULL,
        EventBinaryData text NULL,
        MaxAvailable int NULL,
        CurrUsage int NULL,
        MinUsage int NULL,
        MaxUsage int NULL,
        InfoUnitID int NULL ,
        SysLogTag varchar(60),
        EventLogType varchar(60),
        GenericFileName VarChar(60),
        SystemID int NULL
);

CREATE TABLE IF NOT EXISTS SystemEventsProperties
(
        ID int unsigned not null auto_increment primary key,
        SystemEventID int NULL ,
        ParamName varchar(255) NULL ,
        ParamValue text NULL
);


delete from mysql.user where user="rsyslogd";
delete from mysql.db where User="rsyslogd";

FLUSH PRIVILEGES;
CREATE USER 'rsyslogd'@'localhost' IDENTIFIED BY 'sagdtgghgs6gs';
GRANT ALL PRIVILEGES ON Syslog.* TO 'rsyslogd'@'localhost';
FLUSH PRIVILEGES;


