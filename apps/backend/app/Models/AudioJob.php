<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class AudioJob extends Model
{
    protected $fillable = [
        'status',
        'original_filename',
        'stored_path',
        'mime_type',
        'result',
        'exported_files',
        'processing_logs',
        'error_message',
    ];

    protected function casts(): array
    {
        return [
            'result' => 'array',
            'exported_files' => 'array',
            'processing_logs' => 'array',
        ];
    }
}
