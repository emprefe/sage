INSERT INTO vendors (vendor_key, display_name, documentation_url, status) VALUES
 ('sage-test','SAGE Test Vendor','https://github.com/emprefe/sage','test'),
 ('reference-tools','SAGE Reference Tools','https://github.com/emprefe/sage','test');
INSERT INTO participants (participant_id, display_name, documentation_url, status) VALUES
 ('SAGE.TEST.PYTHON','SAGE Python reference','https://github.com/emprefe/sage','test'),
 ('SAGE.TEST.PHP','SAGE PHP reference','https://github.com/emprefe/sage','test'),
 ('SAGE.TEST.DART','SAGE Dart reference','https://github.com/emprefe/sage','test');
INSERT INTO vendor_participants (vendor_id, participant_id)
 SELECT v.id, p.id FROM vendors v, participants p WHERE v.vendor_key='sage-test' AND p.participant_id LIKE 'SAGE.TEST.%';
