#
# This is a modified version of /usr/share/doc/rsyslog-mysql-*/createDB.sql
#

CREATE DATABASE IF NOT EXISTS  Syslog;

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
) ENGINE=MYISAM;;

ALTER TABLE `SystemEvents`
        ADD INDEX `FromHost` (`FromHost`),
        ADD INDEX `SysLogTag` (`SysLogTag`),
        ADD INDEX `Facility` (`Facility`),
        ADD INDEX `ReceivedAt` (`ReceivedAt`),
        ADD INDEX `DeviceReportedTime` (`DeviceReportedTime`, `FromHost`),
        ADD FULLTEXT INDEX `Message` (`Message`);


CREATE TABLE IF NOT EXISTS SystemEventsProperties
(
        ID int unsigned not null auto_increment primary key,
        SystemEventID int NULL ,
        ParamName varchar(255) NULL ,
        ParamValue text NULL
) ENGINE=MYISAM;;


#
# Useful views.
#

# Only displays relevant information.
CREATE VIEW view_SystemEvents_compact AS
SELECT
    DeviceReportedTime,
    FromHost,
    SysLogTag,
    Message
FROM
    Syslog.SystemEvents
ORDER BY
    DeviceReportedTime DESC;


# How many log messages has been received per day and host.
CREATE VIEW view_SystemEvents_host_sum AS
SELECT
    date(DeviceReportedTime) as day,
    FromHost,
    count(ID)
FROM
    Syslog.SystemEvents
GROUP BY
    FromHost,
    day;

