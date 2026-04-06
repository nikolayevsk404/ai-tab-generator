<?php

namespace App\Jobs;

use App\Models\AudioJob;
use App\Services\AudioProcessingService;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Throwable;

class ProcessAudioJob implements ShouldQueue
{
    use InteractsWithQueue;
    use Queueable;

    public int $timeout = 180;

    public int $tries = 1;

    /**
     * Create a new job instance.
     */
    public function __construct(public readonly int $audioJobId) {}

    /**
     * Execute the job.
     */
    public function handle(AudioProcessingService $audioProcessingService): void
    {
        $audioJob = AudioJob::query()->findOrFail($this->audioJobId);

        $audioJob->update([
            'status' => 'processing',
            'error_message' => null,
        ]);

        try {
            $payload = $audioProcessingService->process($audioJob);
            $gp5Export = $payload['exports']['gp5'] ?? null;
            $storedExports = [];

            if (is_array($gp5Export) && isset($gp5Export['content_base64'], $gp5Export['filename'])) {
                $baseName = Str::slug(pathinfo($audioJob->original_filename, PATHINFO_FILENAME)) ?: 'audio-tab';
                $exportPath = sprintf('audio-exports/%d-%s.gp5', $audioJob->id, $baseName);

                Storage::disk('local')->put($exportPath, base64_decode($gp5Export['content_base64']));

                $storedExports['gp5'] = [
                    'filename' => $gp5Export['filename'],
                    'path' => $exportPath,
                ];
            }

            $audioJob->update([
                'status' => 'done',
                'result' => $payload['tablature'] ?? [],
                'exported_files' => $storedExports,
                'processing_logs' => [
                    'audio_context' => $payload['audio_context'] ?? [],
                    'detected_frequencies' => $payload['detected_frequencies'] ?? [],
                    'detected_notes' => $payload['detected_notes'] ?? [],
                    'raw_segments' => $payload['segments'] ?? [],
                    'warnings' => $payload['warnings'] ?? [],
                ],
                'error_message' => null,
            ]);
        } catch (Throwable $exception) {
            Log::error('Audio processing failed.', [
                'audio_job_id' => $audioJob->id,
                'message' => $exception->getMessage(),
            ]);

            $audioJob->update([
                'status' => 'failed',
                'error_message' => $exception->getMessage(),
            ]);

            throw $exception;
        }
    }
}
