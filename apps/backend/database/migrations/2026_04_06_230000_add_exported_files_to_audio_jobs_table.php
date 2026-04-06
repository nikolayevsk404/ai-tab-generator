<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('audio_jobs', function (Blueprint $table) {
            $table->json('exported_files')->nullable()->after('result');
        });
    }

    public function down(): void
    {
        Schema::table('audio_jobs', function (Blueprint $table) {
            $table->dropColumn('exported_files');
        });
    }
};
