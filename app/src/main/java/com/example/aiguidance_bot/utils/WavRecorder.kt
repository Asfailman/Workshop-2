package com.example.aiguidance_bot.utils

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.io.File
import java.io.FileOutputStream
import java.io.RandomAccessFile

class WavRecorder {

    private var audioRecord: AudioRecord? = null
    private var isRecording = false
    private var recordingThread: Thread? = null

    private val sampleRate = 16000
    private val channelConfig = AudioFormat.CHANNEL_IN_MONO
    private val audioFormat = AudioFormat.ENCODING_PCM_16BIT
    private val bufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat).coerceAtLeast(2048)

    @SuppressLint("MissingPermission")
    fun startRecording(outputFile: File) {
        if (isRecording) return

        audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            sampleRate,
            channelConfig,
            audioFormat,
            bufferSize
        )

        audioRecord?.startRecording()
        isRecording = true

        recordingThread = Thread {
            writeAudioDataToFile(outputFile)
        }
        recordingThread?.start()
    }

    private fun writeAudioDataToFile(outputFile: File) {
        val data = ByteArray(bufferSize)
        val fos = FileOutputStream(outputFile)
        // Reserve 44 bytes for WAV header
        fos.write(ByteArray(44))

        try {
            while (isRecording) {
                val read = audioRecord?.read(data, 0, data.size) ?: 0
                if (read > 0) {
                    fos.write(data, 0, read)
                }
            }
        } finally {
            fos.flush()
            fos.close()
            writeWavHeader(outputFile)
        }
    }

    private fun writeWavHeader(file: File) {
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
        raf.write(intToByteArray(16))
        raf.write(shortToByteArray(1))
        raf.write(shortToByteArray(channels.toShort()))
        raf.write(intToByteArray(sampleRate))
        raf.write(intToByteArray(byteRate))
        raf.write(shortToByteArray((channels * 2).toShort()))
        raf.write(shortToByteArray(16))
        raf.writeBytes("data")
        raf.write(intToByteArray(totalAudioLen.toInt()))
        raf.close()
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

    fun stopRecording() {
        isRecording = false
        try {
            audioRecord?.stop()
            audioRecord?.release()
        } catch (_: Exception) {}
        audioRecord = null
        try {
            recordingThread?.join(1000)
        } catch (_: Exception) {}
        recordingThread = null
    }

    fun isCurrentlyRecording(): Boolean = isRecording
}
