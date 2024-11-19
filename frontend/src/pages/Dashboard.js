import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Search as SearchIcon,
  Description as DocumentIcon,
  QueryStats as QueryIcon,
} from '@mui/icons-material';

function Dashboard() {
  const navigate = useNavigate();

  const features = [
    {
      title: 'Upload Documents',
      description: 'Upload and process SOX compliance documents for analysis',
      icon: <UploadIcon sx={{ fontSize: 40 }} />,
      action: () => navigate('/upload'),
      buttonText: 'Upload Documents',
    },
    {
      title: 'Query Documents',
      description: 'Ask questions about SOX compliance and get accurate answers',
      icon: <SearchIcon sx={{ fontSize: 40 }} />,
      action: () => navigate('/query'),
      buttonText: 'Start Querying',
    },
  ];

  const stats = [
    {
      title: 'Document Processing',
      icon: <DocumentIcon sx={{ fontSize: 30, color: 'primary.main' }} />,
      items: [
        'Supports PDF and DOCX formats',
        'Automatic text extraction and preprocessing',
        'Document chunking for optimal retrieval',
      ],
    },
    {
      title: 'Query System',
      icon: <QueryIcon sx={{ fontSize: 30, color: 'primary.main' }} />,
      items: [
        'Natural language query processing',
        'Context-aware responses',
        'Source citations for transparency',
      ],
    },
  ];

  return (
    <Box sx={{ flexGrow: 1, py: 4 }}>
      <Typography variant="h4" gutterBottom>
        SOX Compliance Document Assistant
      </Typography>

      <Typography variant="subtitle1" color="textSecondary" paragraph>
        Access and analyze SOX compliance documents using advanced RAG technology
      </Typography>

      <Grid container spacing={4} sx={{ mt: 2 }}>
        {/* Main Feature Cards */}
        {features.map((feature, index) => (
          <Grid item xs={12} md={6} key={index}>
            <Paper
              sx={{
                p: 3,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
              }}
            >
              <Box sx={{ color: 'primary.main', mb: 2 }}>{feature.icon}</Box>
              <Typography variant="h6" gutterBottom>
                {feature.title}
              </Typography>
              <Typography color="textSecondary" paragraph>
                {feature.description}
              </Typography>
              <Button
                variant="contained"
                onClick={feature.action}
                startIcon={feature.icon}
                sx={{ mt: 'auto' }}
              >
                {feature.buttonText}
              </Button>
            </Paper>
          </Grid>
        ))}

        {/* System Information */}
        {stats.map((stat, index) => (
          <Grid item xs={12} md={6} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {stat.icon}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {stat.title}
                  </Typography>
                </Box>
                <Box component="ul" sx={{ pl: 2 }}>
                  {stat.items.map((item, itemIndex) => (
                    <Typography
                      component="li"
                      key={itemIndex}
                      color="textSecondary"
                      sx={{ mb: 1 }}
                    >
                      {item}
                    </Typography>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Quick Start Guide */}
      <Paper sx={{ mt: 4, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quick Start Guide
        </Typography>
        <Typography variant="body1" paragraph>
          1. Upload your SOX compliance documents using the upload feature
        </Typography>
        <Typography variant="body1" paragraph>
          2. Wait for the documents to be processed and indexed
        </Typography>
        <Typography variant="body1" paragraph>
          3. Use the query interface to ask questions about your documents
        </Typography>
        <Typography variant="body1">
          4. Review the answers along with their source citations
        </Typography>
      </Paper>
    </Box>
  );
}

export default Dashboard;
