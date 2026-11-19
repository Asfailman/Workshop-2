package com.example.aiguidance_bot.utils

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.io.RandomAccessFile

/**
 * High-reliability 16kHz PCM WAV Audio Recorder for Whisper STT.
 * Features:
 * - Thread-safe synchronization (no race conditions on stop)
 * - VOICE_RECOGNITION audio source with AGC (automatic gain control)
 * - Safe fallback to MIC source
 * - Synchronous header finalizing before callback
 */
class WavRecorder {

    private var audioRecord: AudioRecord? = null
    @Volatile
    private var isRecording = false
    private var recordingThread: Thread? = null
    private var targetFile: File? = null

    private val sampleRate = 16000
    private val channelConfig = AudioFormat.CHANNEL_IN_MONO
    private val audioFormat = AudioFormat.ENCODING_PCM_16BIT

    @SuppressLint("MissingPermission")
    fun startRecording(outputFile: File): Boolean {
        if (isRecording) return true

        val minBuf = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
        val bufferSize = if (minBuf > 0) (minBuf * 2).coerceAtLeast(4096) else 4096

        // Try VOICE_RECOGNITION (ideal for Whisper speech) then fallback to MIC
        val sources = intArrayOf(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            MediaRecorder.AudioSource.MIC,
            MediaRecorder.AudioSource.DEFAULT
        )

        var record: AudioRecord? = null
        for (source in sources) {
            try {
                val candidate = AudioRecord(source, sampleRate, channelConfig, audioFormat, bufferSize)
                if (candidate.state == AudioRecord.STATE_INITIALIZED) {
                    record = candidate
                    break
                } else {
                    candidate.release()
                }
            } catch (e: Exception) {
                Log.w("WavRecorder", "Source $source failed: ${e.message}")
            }
        }

        if (record == null) {
            Log.e("WavRecorder", "Failed to initialize AudioRecord with any audio source.")
            return false
        }

        try {
            record.startRecording()
        } catch (e: Exception) {
            Log.e("WavRecorder", "Failed to start AudioRecord: ${e.message}")
            record.release()
            return false
        }

        audioRecord = record
        isRecording = true
        targetFile = outputFile

        recordingThread = Thread({
            writePcmToWav(outputFile, bufferSize)
        }, "WavRecordingThread")
        recordingThread?.start()

        return true
    }

    private fun writePcmToWav(file: File, bufferSize: Int) {
        val buffer = ByteArray(bufferSize)
        var fos: FileOutputStream? = null
        try {
            fos = FileOutputStream(file)
            // 44-byte placeholder for WAV header
            fos.write(ByteArray(44))

            while (isRecording) {
                val record = audioRecord ?: break
                val read = record.read(buffer, 0, buffer.size)
                if (read > 0) {
                    fos.write(buffer, 0, read)
                }
            }
            fos.flush()
        } catch (e: Exception) {
            Log.e("WavRecorder", "Error writing audio file: ${e.message}")
        } finally {
            try {
                fos?.close()
            } catch (_: Exception) {}
            writeWavHeader(file)
        }
    }

    private fun writeWavHeader(file: File) {
        if (!file.exists() || file.length() < 44) return
        try {
            val totalAudioLen = (file.length() - 44).coerceAtLeast(0)
            val totalDataLen = totalAudioLen + 36
            val channels = 1
            val byteRate = sampleRate * channels * 2

            val raf = RandomAccessFile(file, "rw")
            raf.seek(0)
            raf.writeBytes("RIFF")
            raf.write(intToByteArray(totalDataLen.toInt()))
            raf.writeBytes("WAVE")
            raf.writeBytes("fmt ")
            raf.write(intToByteArray(16))          // Sub-chunk size
            raf.write(shortToByteArray(1.toShort())) // AudioFormat 1 = PCM
            raf.write(shortToByteArray(channels.toShort()))
            raf.write(intToByteArray(sampleRate))
            raf.write(intToByteArray(byteRate))
            raf.write(shortToByteArray((channels * 2).toShort())) // Block align
            raf.write(shortToByteArray(16.toShort()))             // Bits per sample
            raf.writeBytes("data")
            raf.write(intToByteArray(totalAudioLen.toInt()))
            raf.close()
        } catch (e: Exception) {
            Log.e("WavRecorder", "Error finalizing WAV header: ${e.message}")
        }
    }

    private fun intToByteArray(i: Int): ByteArray {
        return byteArrayOf(
            (i and 0xff).toByte(),
            ((i shr 8) and 0xff).toByte(),
            ((i shr 16) and 0xff).toByte(),
            ((i shr 24) and 0xff).toByte()
        )
    }

    private fun shortToByteArray(s: Short): ByteArray {
        return byteArrayOf(
            (s.toInt() and 0xff).toByte(),
            ((s.toInt() shr 8) and 0xff).toByte()
        )
    }

    /**
     * Stops recording and blocks until the audio file has been completely flushed
     * and the WAV header has been written to disk.
     */
    fun stopRecording(): File? {
        if (!isRecording) return targetFile
        isRecording = false

        try {
            audioRecord?.stop()
        } catch (_: Exception) {}
        try {
            audioRecord?.release()
        } catch (_: Exception) {}
        audioRecord = null

        try {
            recordingThread?.join(2500)
        } catch (_: Exception) {}
        recordingThread = null

        val file = targetFile
        targetFile = null
        return file
    }

    fun isCurrentlyRecording(): Boolean = isRecording
}
