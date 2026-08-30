<?php
declare(strict_types=1);

final class SageException extends RuntimeException {
    public string $sageCode;
    public mixed $details;
    public function __construct(string $code, string $message, mixed $details = null) {
        $this->sageCode = $code;
        $this->details = $details;
        parent::__construct($message);
    }
}

function sage_validate_id(string $value): void {
    if (!preg_match('/^[A-Za-z0-9._~-]{1,64}$/', $value)) {
        throw new SageException('INVALID_PARTICIPANT_ID', 'Invalid participant ID');
    }
}

function sage_b64_encode(?string $value): string {
    if ($value === null || $value === '') return '-';
    return rtrim(strtr(base64_encode($value), '+/', '-_'), '=');
}

function sage_b64_decode(string $value): ?string {
    if ($value === '-') return null;
    if (!preg_match('/^[A-Za-z0-9_-]+$/', $value)) throw new SageException('INVALID_EXTENSION_DATA', 'Invalid encoded extension data');
    $decoded = base64_decode(strtr($value, '-_', '+/') . str_repeat('=', (4 - strlen($value) % 4) % 4), true);
    if ($decoded === false || !mb_check_encoding($decoded, 'UTF-8') || strlen($decoded) > 256) throw new SageException('INVALID_EXTENSION_DATA', 'Invalid encoded extension data');
    return $decoded;
}

function sage_parse(string $payload): array {
    if (!mb_check_encoding($payload, 'UTF-8')) throw new SageException('INVALID_UTF8', 'SAGE payload is not valid UTF-8');
    $parts = explode('|', $payload);
    if (($parts[0] ?? '') !== 'SAGE/0.02') throw new SageException('UNSUPPORTED_VERSION', 'Only SAGE/0.02 is supported');
    if (count($parts) < 5 || (count($parts) - 1) % 4 !== 0) throw new SageException('INVALID_RECORD', 'Invalid SAGE participant field count');
    $chain = [];
    $seen = [];
    for ($i = 1; $i < count($parts); $i += 4) {
        $id = $parts[$i]; sage_validate_id($id);
        if (isset($seen[$id])) throw new SageException('DUPLICATE_PARTICIPANT_ID', 'Participant IDs must be unique');
        $seen[$id] = true;
        $chain[] = ['participant_id' => $id, 'ext_data' => [sage_b64_decode($parts[$i + 1]), sage_b64_decode($parts[$i + 2]), sage_b64_decode($parts[$i + 3])]];
    }
    return ['chain' => $chain, 'version' => '0.02'];
}

function sage_serialize(array $record): string {
    if (($record['version'] ?? '0.02') !== '0.02' || empty($record['chain'])) throw new SageException('INVALID_RECORD', 'Unsupported or empty SAGE record');
    $fields = [];
    $seen = [];
    foreach ($record['chain'] as $entry) {
        $id = (string)($entry['participant_id'] ?? ''); sage_validate_id($id);
        if (isset($seen[$id])) throw new SageException('DUPLICATE_PARTICIPANT_ID', 'Participant IDs must be unique');
        $seen[$id] = true;
        $extensions = $entry['ext_data'] ?? [null, null, null];
        if (count($extensions) !== 3) throw new SageException('INVALID_EXTENSION_FIELDS', 'Exactly three extension slots are required');
        $fields[] = $id; foreach ($extensions as $value) { if ($value !== null && strlen((string)$value) > 0 && strlen((string)$value) > 256) throw new SageException('INVALID_EXTENSION_DATA', 'Extension is over capacity'); $fields[] = sage_b64_encode($value); }
    }
    return 'SAGE/0.02|' . implode('|', $fields);
}

function sage_update(array $record, string $participantId, array $extensions = [null, null, null]): array {
    sage_validate_id($participantId);
    if (count($extensions) !== 3) throw new SageException('INVALID_EXTENSION_FIELDS', 'Exactly three extension slots are required');
    $chain = array_values(array_filter($record['chain'], fn(array $entry): bool => $entry['participant_id'] !== $participantId));
    $chain[] = ['participant_id' => $participantId, 'ext_data' => array_values($extensions)];
    return ['chain' => $chain, 'version' => '0.02'];
}
