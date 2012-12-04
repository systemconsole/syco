BEGIN TRANSACTION;
INSERT INTO "escalator_method_data" VALUES(1,1,'defense_center_port','8307');
INSERT INTO "escalator_method_data" VALUES(2,1,'from_address','noreply@noreply.com');
INSERT INTO "escalator_method_data" VALUES(3,1,'notice','2');
INSERT INTO "escalator_method_data" VALUES(4,1,'notice_attach_format','c402cc3e-b531-11e1-9163-406186ea4fc5');
INSERT INTO "escalator_method_data" VALUES(5,1,'URL','');
INSERT INTO "escalator_method_data" VALUES(6,1,'defense_center_ip','');
INSERT INTO "escalator_method_data" VALUES(7,1,'pkcs12','');
INSERT INTO "escalator_method_data" VALUES(8,1,'to_address','${SYCO_ALERT_EMAIL}');
INSERT INTO "escalator_method_data" VALUES(9,1,'notice_report_format','5ceff8ba-1f62-11e1-ab9f-406186ea4fc5');

INSERT INTO "escalators" VALUES(1,'a25423fc-25b4-4b94-a4fc-3d59b96ed939',2,'syco','',1,1,1);
INSERT INTO "schedules" VALUES(1,'889b28bf-eddf-4bb3-ab9d-dac9813f7818',2,'syco','',strftime('%s',datetime(datetime(),'+20 minute')),604800,0,0);

INSERT INTO "targets" VALUES(2,'adcdde54-2314-4084-b0a3-d2a031b5b867',2,'Syco scanning','${SYCO_HOSTS}','',0,NULL,0,1);

INSERT INTO "task_escalators" VALUES(3,2,1,0);

INSERT INTO "task_preferences" VALUES(1,2,'max_checks','4');
INSERT INTO "task_preferences" VALUES(2,2,'max_hosts','20');


INSERT INTO "tasks" VALUES(2,'6cbe2fec-b24c-4be2-b9e9-712ea2eed442',2,'syco',0,0,'','# This file was automatically created by openvasmd, the OpenVAS Manager daemon.
targets = ${SYCO_HOSTS}

begin(SCANNER_SET)
end(SCANNER_SET)

begin(SERVER_PREFS)
 max_hosts = 20
 max_checks = 4
 cgi_path = /cgi-bin:/scripts
 port_range = default
 auto_enable_dependencies = yes
 silent_dependencies = yes
 host_expansion = ip
 reverse_lookup = no
 optimize_test = yes
 safe_checks = yes
 use_mac_addr = no
 unscanned_closed = yes
 save_knowledge_base = yes
 only_test_hosts_whose_kb_we_dont_have = no
 only_test_hosts_whose_kb_we_have = no
 kb_restore = no
 kb_dont_replay_scanners = no
 kb_dont_replay_info_gathering = no
 kb_dont_replay_attacks = no
 kb_dont_replay_denials = no
 kb_max_age = 864000
 log_whole_attack = no
 checks_read_timeout = 5
 network_scan = no
 non_simult_ports = 139, 445
 plugins_timeout = 320
 slice_network_addresses = no
 nasl_no_signature_check = yes
end(SERVER_PREFS)

begin(CLIENTSIDE_USERRULES)
end(CLIENTSIDE_USERRULES)

begin(PLUGINS_PREFS)
 Ping Host[checkbox]:Mark unrechable Hosts as dead (not scanning) = yes
 Login configurations[checkbox]:NTLMSSP = yes
end(PLUGINS_PREFS)

begin(PLUGIN_SET)
end(PLUGIN_SET)

begin(SERVER_INFO)
end(SERVER_INFO)
',2,strftime('%s',datetime(datetime(),'+20 minute')),'',1,2,1,strftime('%s',datetime(datetime(),'+20 minute')),0,0,0,0,0,NULL);
COMMIT;
