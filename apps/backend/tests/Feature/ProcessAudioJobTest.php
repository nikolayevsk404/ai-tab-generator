<?php

namespace Tests\Feature;

use App\Jobs\ProcessAudioJob;
use App\Models\AudioJob;
use App\Services\AudioProcessingService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class ProcessAudioJobTest extends TestCase
{
    use RefreshDatabase;

    public function test_it_processes_audio_and_persists_the_result(): void
    {
        Storage::fake('local');
        Storage::disk('local')->put('audio-uploads/sample.wav', 'fake-audio');

        Http::fake([
            '*' => Http::response([
                'audio_context' => [
                    'tempo_bpm' => 128,
                    'beat_times' => [0.0, 0.469],
                    'guitar_tone' => 'distorted',
                ],
                'detected_frequencies' => [
                    ['time' => 0.0, 'frequency' => 82.41],
                ],
                'detected_notes' => [
                    ['time' => 0.0, 'quantized_time' => 0.0, 'note' => 'E2'],
                ],
                'tablature' => [
                    ['string' => 6, 'fret' => 0, 'time' => 0.0, 'detected_time' => 0.01, 'note' => 'E2'],
                ],
                'segments' => [],
                'exports' => [
                    'gp5' => [
                        'filename' => 'sample.gp5',
                        'content_base64' => base64_encode('fake-gp5-binary'),
                    ],
                ],
            ]),
        ]);

        $audioJob = AudioJob::query()->create([
            'status' => 'pending',
            'original_filename' => 'sample.wav',
            'stored_path' => 'audio-uploads/sample.wav',
            'mime_type' => 'audio/wav',
        ]);

        (new ProcessAudioJob($audioJob->id))->handle(app(AudioProcessingService::class));

        $audioJob->refresh();

        $this->assertSame('done', $audioJob->status);
        $this->assertSame('E2', $audioJob->result[0]['note']);
        $this->assertSame('distorted', $audioJob->processing_logs['audio_context']['guitar_tone']);
        $this->assertSame('sample.gp5', $audioJob->exported_files['gp5']['filename']);
        Storage::disk('local')->assertExists($audioJob->exported_files['gp5']['path']);
    }
}
