<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Jobs\ProcessAudioJob;
use App\Models\AudioJob;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Symfony\Component\HttpFoundation\StreamedResponse;

class UploadController extends Controller
{
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'audio' => ['required', 'file', 'mimes:mp3,wav'],
        ]);

        $file = $validated['audio'];
        $storedPath = $file->store('audio-uploads');

        $audioJob = AudioJob::query()->create([
            'status' => 'pending',
            'original_filename' => $file->getClientOriginalName(),
            'stored_path' => $storedPath,
            'mime_type' => $file->getClientMimeType(),
        ]);

        ProcessAudioJob::dispatch($audioJob->id);

        return response()->json([
            'job_id' => $audioJob->id,
            'status' => $audioJob->status,
        ], 202);
    }

    public function show(AudioJob $audioJob): JsonResponse
    {
        return response()->json([
            'job_id' => $audioJob->id,
            'status' => $audioJob->status,
            'filename' => $audioJob->original_filename,
            'result' => $audioJob->result,
            'exports' => [
                'gp5' => $audioJob->exported_files['gp5'] ?? null,
                'gp5_download_url' => ($audioJob->exported_files['gp5'] ?? null) !== null
                    ? route('audio-jobs.export.gp5', $audioJob)
                    : null,
            ],
            'logs' => $audioJob->processing_logs,
            'error_message' => $audioJob->error_message,
            'created_at' => $audioJob->created_at?->toIso8601String(),
            'updated_at' => $audioJob->updated_at?->toIso8601String(),
        ]);
    }

    public function downloadGp5(AudioJob $audioJob): StreamedResponse
    {
        $path = $audioJob->exported_files['gp5']['path'] ?? null;

        abort_if($path === null, 404, 'GP5 export not found for this job.');
        abort_unless(Storage::disk('local')->exists($path), 404, 'GP5 export file is missing.');

        return Storage::disk('local')->download(
            $path,
            $audioJob->exported_files['gp5']['filename'] ?? 'tab-export.gp5',
            ['Content-Type' => 'application/octet-stream']
        );
    }
}
