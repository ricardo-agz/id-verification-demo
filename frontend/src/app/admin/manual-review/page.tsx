'use client';

import React, { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  Grid,
  Box,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Button
} from '@mui/material';
import { CheckCircle, Error, Pending } from '@mui/icons-material';
import useFetch from '@/lib/hooks/use-fetch';
import useApi from '@/lib/hooks/use-api';

interface ExtractedDocumentData {
  id: string;
  document_type: string;
  extracted_data: Record<string, any>;
  document_image_s3_url: string;
  viewable_url?: string;
  needs_manual_review: boolean;
  manual_review_completed: boolean;
}

export default function ManualReviewPage() {
  const [selectedDocument, setSelectedDocument] = useState<ExtractedDocumentData | null>(null);
  const { data, error, loading, refresh } = useFetch<ExtractedDocumentData[]>(`${process.env.NEXT_PUBLIC_BACKEND_URL}/documents-to-review`);
  const updateApi = useApi<ExtractedDocumentData>('/api/documents');

  const handleApprove = async (documentId: string) => {
    await updateApi.execute('PUT', {
      id: documentId,
      manual_review_completed: true,
      needs_manual_review: false
    });
    refresh();
    setSelectedDocument(null);
  };

  const handleReject = async (documentId: string) => {
    await updateApi.execute('PUT', {
      id: documentId,
      manual_review_completed: true,
      needs_manual_review: false,
      rejected: true
    });
    refresh();
    setSelectedDocument(null);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  const documents = data?.data || [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Manual Document Review
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={selectedDocument ? 6 : 12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Documents Pending Review ({documents.length})
            </Typography>
            <Stack spacing={2}>
              {documents.map((doc) => (
                <Card
                  key={doc.id}
                  sx={{
                    cursor: 'pointer',
                    border: selectedDocument?.id === doc.id ? 2 : 0,
                    borderColor: 'primary.main'
                  }}
                  onClick={() => setSelectedDocument(doc)}
                >
                  <CardContent>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} sm={4}>
                        <CardMedia
                          component="img"
                          height="140"
                          image={doc.document_image_s3_url || '/placeholder.png'}
                          alt={doc.document_type}
                          sx={{ objectFit: 'contain', bgcolor: 'black' }}
                        />
                      </Grid>
                      <Grid item xs={12} sm={8}>
                        <Typography variant="h6" gutterBottom>
                          {doc.document_type}
                        </Typography>
                        <Chip
                          icon={<Pending />}
                          label="Needs Review"
                          color="warning"
                          size="small"
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          ID: {doc.id}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              ))}
            </Stack>
          </Paper>
        </Grid>

        {selectedDocument && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Document Details
              </Typography>
              <Box sx={{ mb: 2 }}>
                <img
                  src={selectedDocument.document_image_s3_url || '/placeholder.png'}
                  alt={selectedDocument.document_type}
                  style={{
                    width: '100%',
                    maxHeight: '400px',
                    objectFit: 'contain',
                    backgroundColor: 'black'
                  }}
                />
              </Box>

              <Typography variant="subtitle1" gutterBottom>
                Extracted Information:
              </Typography>
              <Box sx={{ mb: 3 }}>
                {Object.entries(selectedDocument.extracted_data).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Typography variant="subtitle2" component="span">
                      {key}:{' '}
                    </Typography>
                    <Typography variant="body2" component="span">
                      {typeof value === 'object'
                        ? JSON.stringify(value, null, 2)
                        : String(value)}
                    </Typography>
                  </Box>
                ))}
              </Box>

              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckCircle />}
                  onClick={() => handleApprove(selectedDocument.id)}
                  fullWidth
                >
                  Approve
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  startIcon={<Error />}
                  onClick={() => handleReject(selectedDocument.id)}
                  fullWidth
                >
                  Reject
                </Button>
              </Stack>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
}