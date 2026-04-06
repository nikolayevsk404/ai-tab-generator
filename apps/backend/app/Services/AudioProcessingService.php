<?php

namespace App\Services;

use App\Models\AudioJob;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\RequestException;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use RuntimeException;

class AudioProcessingService
{
    /**
     * @return array<string, mixed>
     *
     * @throws ConnectionException
     * @throws RequestException
     */
    public function process(AudioJob $audioJob): array
    {
        $disk = Storage::disk('local');

        if (! $disk->exists($audioJob->stored_path)) {
            throw new RuntimeException('Uploaded audio file could not be found.');
        }

        $response = Http::timeout((int) env('AI_SERVICE_TIMEOUT', 120))
            ->acceptJson()
            ->attach(
                'audio',
                $disk->get($audioJob->stored_path),
                basename($audioJob->stored_path)
            )
            ->post(rtrim((string) env('AI_SERVICE_URL', 'http://127.0.0.1:8001'), '/').'/process-audio', [
                'job_id' => $audioJob->id,
                'filename' => $audioJob->original_filename,
            ]);

        $response->throw();

        return $response->json();
    }
}
