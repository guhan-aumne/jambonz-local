-- 1. Add missing system_information
INSERT INTO system_information (domain_name, sip_domain_name, monitoring_domain_name, private_network_cidr, log_level)
VALUES ('jambonz.local', 'sip.jambonz.local', 'monitoring.jambonz.local', '172.18.0.0/16', 'debug');

-- 2. Create "Local Webhook" Application
-- Using UUIDs:
-- App SID: 597148a0-7b00-47b2-95f2-4503730e23ad
-- Call Hook SID: e786934c-6a7f-44e2-861c-81498f328109
-- Status Hook SID: 9be0a4f5-7e05-4c6e-88dc-c16f272a2754

INSERT IGNORE INTO webhooks (webhook_sid, url, method)
VALUES
('e786934c-6a7f-44e2-861c-81498f328109', 'http://webhook:3002/call', 'POST'),
('9be0a4f5-7e05-4c6e-88dc-c16f272a2754', 'http://webhook:3002/call-status', 'POST');

INSERT IGNORE INTO applications (
    application_sid, 
    account_sid, 
    name, 
    call_hook_sid, 
    call_status_hook_sid, 
    speech_synthesis_vendor, 
    speech_synthesis_language, 
    speech_synthesis_voice, 
    speech_recognizer_vendor, 
    speech_recognizer_language
)
VALUES (
    '597148a0-7b00-47b2-95f2-4503730e23ad', 
    '9351f46a-678c-43f5-b8a6-d4eb58d131af', 
    'Local Webhook', 
    'e786934c-6a7f-44e2-861c-81498f328109', 
    '9be0a4f5-7e05-4c6e-88dc-c16f272a2754', 
    'google', 
    'en-US', 
    'en-US-Wavenet-C', 
    'google', 
    'en-US'
);

-- 3. Update Default Account to use this app for outbound device calling
UPDATE accounts 
SET device_calling_application_sid = '597148a0-7b00-47b2-95f2-4503730e23ad'
WHERE account_sid = '9351f46a-678c-43f5-b8a6-d4eb58d131af';
