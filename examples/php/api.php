<?php
declare(strict_types=1);
require_once __DIR__ . '/SageImage.php';
header('Content-Type: application/json; charset=UTF-8');
try {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST' || empty($_FILES['image']['tmp_name'])) throw new SageException('INVALID_REQUEST', 'POST an image file');
    $participant = (string)($_POST['participant_id'] ?? 'SAGE.TEST.PHP');
    $extensions = [(string)($_POST['ext_data_1'] ?? ''), (string)($_POST['ext_data_2'] ?? ''), (string)($_POST['ext_data_3'] ?? '')];
    $bytes = file_get_contents($_FILES['image']['tmp_name']); if ($bytes === false) throw new SageException('READ_FAILED', 'Unable to read image');
    $mime = (new finfo(FILEINFO_MIME_TYPE))->buffer($bytes); $prior = sage_image_decode($bytes, $mime); $operation = (string)($_POST['operation'] ?? 'none'); $transformed = sage_image_transform($bytes, $mime, $operation); $record = $prior ? sage_update($prior, $participant, $extensions) : ['version'=>'0.02','chain'=>[['participant_id'=>$participant,'ext_data'=>$extensions]]];
    $output = sage_image_encode($transformed, $record, $mime); $check = sage_image_decode($output, $mime); if (sage_serialize($check) !== sage_serialize($record)) throw new SageException('SELF_CHECK_FAILED', 'Encoded output did not decode identically');
    echo json_encode(['status'=>'SUCCESS','format'=>$mime,'operation'=>$operation,'prior_record'=>$prior,'record'=>$check,'serialized'=>sage_serialize($check),'download_name'=>'sage-output.'.sage_image_extension($mime),'output_base64'=>base64_encode($output)], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
} catch (SageException $e) { http_response_code(400); echo json_encode(['status'=>'ERROR','error_code'=>$e->sageCode,'error_details'=>$e->getMessage()], JSON_UNESCAPED_UNICODE); }
catch (Throwable $e) { http_response_code(500); echo json_encode(['status'=>'ERROR','error_code'=>'INTERNAL_ERROR','error_details'=>'Unexpected server error']); }
