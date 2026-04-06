<?php

use App\Http\Controllers\Api\UploadController;
use Illuminate\Support\Facades\Route;

Route::post('/upload', [UploadController::class, 'store']);
Route::get('/result/{audioJob}', [UploadController::class, 'show']);
Route::get('/result/{audioJob}/export/gp5', [UploadController::class, 'downloadGp5'])->name('audio-jobs.export.gp5');
