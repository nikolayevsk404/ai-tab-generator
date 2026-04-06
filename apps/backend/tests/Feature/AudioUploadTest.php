<?php

namespace Tests\Feature;

use App\Jobs\ProcessAudioJob;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Queue;
use Tests\TestCase;

class AudioUploadTest extends TestCase
{
    use RefreshDatabase;

    public function test_it_creates_an_audio_job_and_dispatches_processing(): void
    {
        Queue::fake();

        $response = $this->postJson('/api/upload', [
            'audio' => UploadedFile::fake()->create('riff.wav', 32, 'audio/wav'),
        ]);

        $response->assertAccepted()
            ->assertJsonPath('status', 'pending');

        $this->assertDatabaseCount('audio_jobs', 1);
        Queue::assertPushed(ProcessAudioJob::class);
    }
}
