'use client'

import React, { useState, useRef, useEffect } from 'react'
import {
  Button,
  Container,
  Typography,
  Box,
  Paper,
  Stack,
  Alert,
  IconButton
} from '@mui/material'
import {
  PhotoCamera,
  FileUpload,
  Close as CloseIcon
} from '@mui/icons-material'
import useApi from "@/lib/hooks/use-api"

interface DocumentProcessingResponse {
  document_type: string;
  extracted_data: any;
  metadata: {
    classification: any;
    extracted_data: any;
  } | null;
}

export default function DocumentScanner() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [isUsingCamera, setIsUsingCamera] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isCameraReady, setIsCameraReady] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    // Cleanup function to stop camera stream when component unmounts
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [stream])

  // Add event listener for when video is ready to play
  useEffect(() => {
    const videoElement = videoRef.current
    if (videoElement) {
      const handleCanPlay = () => {
        setIsCameraReady(true)
      }
      videoElement.addEventListener('canplay', handleCanPlay)
      return () => {
        videoElement.removeEventListener('canplay', handleCanPlay)
      }
    }
  }, [isUsingCamera])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      processSelectedFile(file)
    }
  }

  const processSelectedFile = (file: File) => {
    setSelectedFile(file)
    const reader = new FileReader()
    reader.onloadend = () => {
      setSelectedImage(reader.result as string)
    }
    reader.readAsDataURL(file)
    setUploadStatus('idle')
    setErrorMessage(null)
  }

  const startCamera = async () => {
    try {
      setIsUsingCamera(true)

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      })

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
        setStream(mediaStream)
        setIsUsingCamera(true)
        // Reset states when starting camera
        setSelectedImage(null)
        setSelectedFile(null)
        setUploadStatus('idle')
        setErrorMessage(null)
      }
    } catch (error) {
      console.error('Error accessing camera:', error)
      setErrorMessage('Unable to access camera. Please ensure you have granted camera permissions.')
      setIsUsingCamera(false)
    }
  }

  const capturePhoto = () => {
    if (videoRef.current && isCameraReady) {
      const video = videoRef.current
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      const context = canvas.getContext('2d')
      if (context) {
        context.drawImage(video, 0, 0, canvas.width, canvas.height)

        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], "captured-image.jpg", {
              type: "image/jpeg",
              lastModified: Date.now()
            })
            processSelectedFile(file)
          }
        }, 'image/jpeg', 0.95)
      }

      stopCamera()
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
    setIsUsingCamera(false)
    setIsCameraReady(false)
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select or capture an image first')
      return
    }

    setUploadStatus('loading')
    setErrorMessage(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/process`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        if (response.status === 400 && data.detail === "File must be an image") {
          throw new Error("Please upload a valid image file")
        }
        else if (response.status === 422) {
          switch (data.detail) {
            case "Unsupported document type":
              throw new Error("This type of document is not supported. Please upload a valid ID document")
            case "Document not recognized":
              throw new Error("Unable to recognize the document. Please ensure you're uploading a clear photo of a valid ID")
            default:
              throw new Error(data.detail)
          }
        }
        throw new Error(data.detail || 'Upload failed')
      }

      setUploadStatus('success')
      console.log('Document processed successfully:', data)
    } catch (error) {
      console.error('Error during upload:', error)
      setUploadStatus('error')
      setErrorMessage(
        error instanceof Error ?
          error.message :
          'An unexpected error occurred while processing your document'
      )
    }
  }

  const handleRetake = () => {
    setSelectedImage(null)
    setSelectedFile(null)
    setUploadStatus('idle')
    setErrorMessage(null)
    startCamera()
  }

  const handleSelectNew = () => {
    setSelectedImage(null)
    setSelectedFile(null)
    setUploadStatus('idle')
    setErrorMessage(null)
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          ID Verification
        </Typography>

        <Stack spacing={2}>
          {/* Show camera/file buttons only when not using camera and no image selected */}
          {!isUsingCamera && !selectedImage && (
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                fullWidth
                startIcon={<FileUpload />}
                onClick={() => fileInputRef.current?.click()}
              >
                Select File
              </Button>

              <Button
                variant="contained"
                fullWidth
                color="success"
                startIcon={<PhotoCamera />}
                onClick={startCamera}
              >
                Use Camera
              </Button>
            </Stack>
          )}

          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            ref={fileInputRef}
            style={{ display: 'none' }}
          />

          {/* Camera preview */}
          {isUsingCamera && (
            <Box sx={{
              position: 'relative',
              backgroundColor: 'black',
              borderRadius: 1,
              overflow: 'hidden'
            }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                style={{
                  width: '100%',
                  height: 'auto',
                  maxHeight: '70vh',
                  objectFit: 'cover',
                  display: 'block'
                }}
              />
              <Stack
                spacing={1}
                sx={{
                  pt: 2,
                  position: 'relative',
                  zIndex: 1
                }}
                style={{
                    display: 'flex',
                    justifyContent: 'center',
                    backgroundColor: 'white'
                }}
              >
                <Button
                  variant="contained"
                  onClick={capturePhoto}
                  fullWidth
                  disabled={!isCameraReady}
                  color="success"
                >
                  {isCameraReady ? 'Take Picture' : 'Preparing Camera...'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={stopCamera}
                  startIcon={<CloseIcon />}
                  fullWidth
                  color="error"
                >
                  Cancel
                </Button>
              </Stack>
            </Box>
          )}

          {/* Selected/captured image preview */}
          {selectedImage && !isUsingCamera && (
            <Stack spacing={2}>
              <Box
                component="img"
                src={selectedImage}
                alt="Selected ID"
                sx={{
                  width: '100%',
                  height: 'auto',
                  maxHeight: '70vh',
                  objectFit: 'contain',
                  borderRadius: 1,
                  border: '1px solid',
                  borderColor: 'divider',
                  backgroundColor: 'black'
                }}
              />
              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  fullWidth
                  disabled={uploadStatus === 'loading'}
                  onClick={handleUpload}
                >
                  {uploadStatus === 'loading' ? 'Processing...' : 'Upload ID'}
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={selectedFile?.type === 'image/jpeg' ? handleRetake : handleSelectNew}
                >
                  {selectedFile?.type === 'image/jpeg' ? 'Retake' : 'Select New'}
                </Button>
              </Stack>
            </Stack>
          )}

          {errorMessage && (
            <Alert severity="error" onClose={() => setErrorMessage(null)}>
              {errorMessage}
            </Alert>
          )}

          {uploadStatus === 'success' && (
            <Alert severity="success">
              Document processed successfully!
            </Alert>
          )}
        </Stack>
      </Paper>
    </Container>
  )
}