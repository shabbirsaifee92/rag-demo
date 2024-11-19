import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Chip,
  Card,
  CardContent,
  IconButton,
  Collapse,
  Grid,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Send as SendIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  Psychology as PsychologyIcon,
  Assessment as AssessmentIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function QueryInterface() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [responses, setResponses] = useState([]);
  const [expandedSource, setExpandedSource] = useState(null);
  const [expandedAnalysis, setExpandedAnalysis] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_URL}/query`, {
        query: query.trim(),
        include_analysis: true,
      });

      setResponses((prev) => [
        {
          question: query,
          ...response.data,
          timestamp: new Date().toISOString(),
        },
        ...prev,
      ]);
      setQuery('');
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Error processing query. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleSource = (index) => {
    setExpandedSource(expandedSource === index ? null : index);
  };

  const toggleAnalysis = (index) => {
    setExpandedAnalysis(expandedAnalysis === index ? null : index);
  };

  const renderQueryAnalysis = (analysis) => (
    <Card sx={{ mt: 2, bgcolor: 'grey.50' }}>
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <PsychologyIcon sx={{ mr: 1 }} />
              <Typography variant="subtitle1">Query Type:</Typography>
            </Box>
            <Chip
              label={analysis.query_type}
              color="primary"
              variant="outlined"
              sx={{ mr: 1 }}
            />
            <Chip
              label={`Complexity: ${analysis.complexity}`}
              color="secondary"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <AssessmentIcon sx={{ mr: 1 }} />
              <Typography variant="subtitle1">Confidence Score:</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ width: '100%', mr: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={analysis.confidence_score * 100}
                  sx={{ height: 10, borderRadius: 5 }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                {(analysis.confidence_score * 100).toFixed(1)}%
              </Typography>
            </Box>
          </Grid>
          {analysis.temporal_context.has_temporal_aspect && (
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TimerIcon sx={{ mr: 1 }} />
                <Typography variant="subtitle1">Temporal Context:</Typography>
              </Box>
              {analysis.temporal_context.temporal_references.map((ref, idx) => (
                <Chip
                  key={idx}
                  label={ref.text}
                  variant="outlined"
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Grid>
          )}
          {analysis.entities.length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Identified Entities:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {analysis.entities.map((entity, idx) => (
                  <Tooltip
                    key={idx}
                    title={`Type: ${entity.type}`}
                    placement="top"
                  >
                    <Chip
                      label={entity.text}
                      variant="outlined"
                      size="small"
                      color="info"
                    />
                  </Tooltip>
                ))}
              </Box>
            </Grid>
          )}
        </Grid>
      </CardContent>
    </Card>
  );

  const renderSourceReferences = (sources) => (
    <Box sx={{ bgcolor: 'action.hover', p: 2, borderRadius: 1 }}>
      <Typography variant="subtitle1" gutterBottom>
        Source References:
      </Typography>
      <List>
        {sources.map((source, sourceIndex) => (
          <Card key={sourceIndex} sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle2">
                  Document: {source.document}
                </Typography>
                <Chip
                  label={`Page ${source.page}`}
                  size="small"
                  variant="outlined"
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip
                  label={`Type: ${source.relevance_type}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label={`Confidence: ${(source.confidence * 100).toFixed(1)}%`}
                  size="small"
                  color={source.confidence > 0.7 ? 'success' : 'warning'}
                  variant="outlined"
                />
              </Box>
              <Typography
                variant="body2"
                sx={{
                  bgcolor: 'background.paper',
                  p: 1,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                }}
              >
                {source.excerpt}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Query SOX Documents
      </Typography>

      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{ p: 2, mb: 4, display: 'flex', alignItems: 'flex-start', gap: 2 }}
      >
        <TextField
          fullWidth
          multiline
          rows={3}
          variant="outlined"
          placeholder="Ask a question about SOX compliance..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <Button
          type="submit"
          variant="contained"
          disabled={loading || !query.trim()}
          sx={{ minWidth: 100, height: 56 }}
        >
          {loading ? (
            <CircularProgress size={24} />
          ) : (
            <>
              Send
              <SendIcon sx={{ ml: 1 }} />
            </>
          )}
        </Button>
      </Paper>

      {error && (
        <Paper sx={{ p: 2, mb: 4, bgcolor: 'error.light', color: 'error.contrastText' }}>
          <Typography>{error}</Typography>
        </Paper>
      )}

      <List>
        {responses.map((response, index) => (
          <Paper key={index} sx={{ mb: 3, overflow: 'hidden' }}>
            <ListItem>
              <ListItemText
                primary={
                  <Typography variant="h6" gutterBottom>
                    Q: {response.question}
                  </Typography>
                }
                secondary={
                  <Box sx={{ mt: 2 }}>
                    <Typography component="div" variant="body1" sx={{ mb: 2 }}>
                      <ReactMarkdown>{response.answer}</ReactMarkdown>
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      <Chip
                        label={`Confidence: ${(response.confidence * 100).toFixed(1)}%`}
                        color={response.confidence > 0.7 ? 'success' : 'warning'}
                        variant="outlined"
                      />
                      <Chip
                        label={`Sources: ${response.sources.length}`}
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                }
              />
            </ListItem>

            <Divider />

            <Box>
              <ListItem
                button
                onClick={() => toggleAnalysis(index)}
                sx={{ bgcolor: 'background.default' }}
              >
                <ListItemText primary="Query Analysis" />
                <IconButton edge="end">
                  {expandedAnalysis === index ? (
                    <ExpandLessIcon />
                  ) : (
                    <ExpandMoreIcon />
                  )}
                </IconButton>
              </ListItem>
              <Collapse in={expandedAnalysis === index}>
                <Box sx={{ p: 2 }}>
                  {renderQueryAnalysis(response.query_analysis)}
                </Box>
              </Collapse>
            </Box>

            <Divider />

            <Box>
              <ListItem
                button
                onClick={() => toggleSource(index)}
                sx={{ bgcolor: 'background.default' }}
              >
                <ListItemText primary="Source References" />
                <IconButton edge="end">
                  {expandedSource === index ? (
                    <ExpandLessIcon />
                  ) : (
                    <ExpandMoreIcon />
                  )}
                </IconButton>
              </ListItem>
              <Collapse in={expandedSource === index}>
                <Box sx={{ p: 2 }}>
                  {renderSourceReferences(response.sources)}
                </Box>
              </Collapse>
            </Box>
          </Paper>
        ))}
      </List>
    </Box>
  );
}

export default QueryInterface;
