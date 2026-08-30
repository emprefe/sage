<?php
declare(strict_types=1);
require_once __DIR__ . '/SageCore.php';

function sage_image_extension(string $mime): string { return match ($mime) { 'image/png' => 'png', 'image/jpeg' => 'jpg', 'image/webp' => 'webp', default => throw new SageException('UNSUPPORTED_FORMAT', 'Only PNG, JPEG, and WebP are supported') }; }

function sage_image_encode(string $bytes, array $record, string $mime): string {
    $payload = sage_serialize($record);
    if ($mime === 'image/png') return sage_png_write($bytes, $payload);
    if ($mime === 'image/jpeg') return sage_jpeg_write($bytes, $payload);
    if ($mime === 'image/webp') return sage_webp_write($bytes, $payload);
    throw new SageException('UNSUPPORTED_FORMAT', 'Unsupported image format');
}

function sage_image_decode(string $bytes, string $mime): ?array {
    try {
        $payload = $mime === 'image/png' ? sage_png_read($bytes) : ($mime === 'image/jpeg' ? sage_jpeg_read($bytes) : sage_webp_read($bytes));
        return $payload === null ? null : sage_parse($payload);
    } catch (SageException $e) { throw $e; }
    catch (Throwable $e) { throw new SageException('DAMAGED_METADATA', 'Image metadata is damaged'); }
}

function sage_image_transform(string $bytes, string $mime, string $operation): string {
    if ($operation === 'none') return $bytes;
    $image = @imagecreatefromstring($bytes);
    if (!$image) throw new SageException('IMAGE_TRANSFORM_FAILED', 'Unable to decode image for transformation');
    if ($operation === 'resize_50') {
        $width = max(1, (int)floor(imagesx($image) / 2)); $height = max(1, (int)floor(imagesy($image) / 2));
        $resized = imagecreatetruecolor($width, $height);
        imagealphablending($resized, false); imagesavealpha($resized, true);
        imagecopyresampled($resized, $image, 0, 0, 0, 0, $width, $height, imagesx($image), imagesy($image));
        imagedestroy($image); $image = $resized;
    } elseif ($operation === 'brightness_10') {
        imagefilter($image, IMG_FILTER_BRIGHTNESS, 10);
    } else {
        imagedestroy($image); throw new SageException('INVALID_OPERATION', 'Unknown image operation');
    }
    ob_start();
    $ok = match ($mime) {
        'image/png' => imagepng($image, null, 9),
        'image/jpeg' => imagejpeg($image, null, 90),
        'image/webp' => function_exists('imagewebp') ? imagewebp($image, null, 90) : false,
        default => false,
    };
    $output = ob_get_clean(); imagedestroy($image);
    if (!$ok || $output === false) throw new SageException('IMAGE_TRANSFORM_FAILED', 'Unable to encode transformed image');
    return $output;
}

function sage_png_chunks(string $bytes): array {
    if (substr($bytes, 0, 8) !== "\x89PNG\r\n\x1a\n") throw new SageException('INVALID_IMAGE', 'Not a PNG');
    $chunks = []; for ($p = 8, $n = strlen($bytes); $p + 12 <= $n;) { $len = unpack('N', substr($bytes, $p, 4))[1]; $end = $p + 12 + $len; if ($end > $n) throw new SageException('DAMAGED_METADATA', 'Truncated PNG'); $chunks[] = [substr($bytes, $p + 4, 4), substr($bytes, $p + 8, $len)]; $p = $end; if ($chunks[count($chunks)-1][0] === 'IEND') break; } return $chunks;
}
function sage_png_chunk(string $type, string $data): string { return pack('N', strlen($data)) . $type . $data . pack('N', crc32($type . $data)); }
function sage_png_itxt(string $payload): string { return sage_png_chunk('iTXt', "SAGE\0\0\0\0\0" . $payload); }
function sage_png_read(string $bytes): ?string { $found = []; foreach (sage_png_chunks($bytes) as [$type, $data]) if ($type === 'iTXt' && str_starts_with($data, "SAGE\0")) $found[] = substr($data, 9); if (!$found) return null; if (count(array_unique($found)) !== 1) throw new SageException('CONFLICTING_METADATA', 'Conflicting SAGE metadata'); return $found[0]; }
function sage_png_write(string $bytes, string $payload): string { $out = "\x89PNG\r\n\x1a\n"; $inserted = false; foreach (sage_png_chunks($bytes) as [$type, $data]) { if ($type === 'iTXt' && str_starts_with($data, "SAGE\0")) { if (!$inserted) { $out .= sage_png_itxt($payload); $inserted = true; } continue; } $out .= sage_png_chunk($type, $data); if ($type === 'IHDR' && !$inserted) { $out .= sage_png_itxt($payload); $inserted = true; } } return $out; }

function sage_xmp(string $payload): string { return "http://ns.adobe.com/xap/1.0/\0<?xpacket begin=\xef\xbb\xbf?><x:xmpmeta xmlns:x=\"adobe:ns:meta/\"><rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\"><rdf:Description xmlns:sage=\"https://sage-protocol.org/ns/0.02/\"><sage:record>" . htmlspecialchars($payload, ENT_XML1 | ENT_QUOTES, 'UTF-8') . "</sage:record></rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end=\"w\"?>"; }
function sage_xmp_record(string $xmp): string { if (!preg_match('/<sage:record>([^<]*)<\/sage:record>/', $xmp, $m)) throw new SageException('INVALID_XMP', 'SAGE record missing from XMP'); return html_entity_decode($m[1], ENT_XML1 | ENT_QUOTES, 'UTF-8'); }
function sage_jpeg_segments(string $bytes): array { if (substr($bytes, 0, 2) !== "\xff\xd8") throw new SageException('INVALID_IMAGE', 'Not a JPEG'); $out=[]; for ($p=2,$n=strlen($bytes);$p+4<=$n;) { if (ord($bytes[$p])!==255) throw new SageException('DAMAGED_METADATA','Malformed JPEG'); $marker=ord($bytes[$p+1]); if ($marker===218) {$out[]=[$p,$n,$marker,''];break;} $len=unpack('n',substr($bytes,$p+2,2))[1];$end=$p+2+$len;if($end>$n||$len<2)throw new SageException('DAMAGED_METADATA','Truncated JPEG');$out[]=[$p,$end,$marker,substr($bytes,$p+4,$len-2)];$p=$end;}return $out; }
function sage_jpeg_read(string $bytes): ?string { $found=[]; foreach(sage_jpeg_segments($bytes) as [$s,$e,$m,$d]) if($m===225&&str_starts_with($d,"http://ns.adobe.com/xap/1.0/\0"))$found[]=sage_xmp_record($d);if(!$found)return null;if(count(array_unique($found))!==1)throw new SageException('CONFLICTING_METADATA','Conflicting SAGE metadata');return $found[0]; }
function sage_jpeg_write(string $bytes,string $payload):string{$segment="\xff\xe1".pack('n',strlen(sage_xmp($payload))+2).sage_xmp($payload);$out="\xff\xd8";$done=false;foreach(sage_jpeg_segments($bytes)as[$s,$e,$m,$d]){if($m===225&&str_starts_with($d,"http://ns.adobe.com/xap/1.0/\0")){if(!$done){$out.=$segment;$done=true;}continue;}if($m===218&&!$done){$out.=$segment;$done=true;}$out.=substr($bytes,$s,$e-$s);}return$out;}
function sage_webp_read(string $bytes): ?string { if(substr($bytes,0,4)!=='RIFF'||substr($bytes,8,4)!=='WEBP')throw new SageException('INVALID_IMAGE','Not a WebP');$found=[];for($p=12,$n=strlen($bytes);$p+8<=$n;){$len=unpack('V',substr($bytes,$p+4,4))[1];$d=substr($bytes,$p+8,$len);if(substr($bytes,$p,4)==='XMP ')$found[]=sage_xmp_record($d);$p+=8+$len+($len&1);}if(!$found)return null;if(count(array_unique($found))!==1)throw new SageException('CONFLICTING_METADATA','Conflicting SAGE metadata');return$found[0];}
function sage_webp_write(string $bytes,string $payload):string{$chunks=[];for($p=12,$n=strlen($bytes);$p+8<=$n;){$len=unpack('V',substr($bytes,$p+4,4))[1];$chunks[]=[$p,$p+8+$len+($len&1),substr($bytes,$p,4)];$p=$chunks[count($chunks)-1][1];}$x=sage_xmp($payload);$chunk='XMP '.pack('V',strlen($x)).$x.((strlen($x)&1)?"\0":'');$out=substr($bytes,0,12);$done=false;foreach($chunks as[$s,$e,$t]){if($t==='XMP '){if(!$done){$out.=$chunk;$done=true;}continue;}$out.=substr($bytes,$s,$e-$s);}if(!$done)$out.=$chunk;return substr_replace($out,pack('V',strlen($out)-8),4,4);}
