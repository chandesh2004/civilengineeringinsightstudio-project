import React, { useState } from 'react';
import axios from 'axios';
import './CivilEngineeringStudio.css';

const CivilEngineeringStudio = () => {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [scenario, setScenario] = useState('Material Identification');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('analysis');

  const scenarios = [
    'Material Identification',
    'Project Documentation',
    'Structural Analysis'
  ];

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleScenarioChange = (e) => {
    setScenario(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!image) {
      setError('Please select an image');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', image);
      formData.append('scenario', scenario);

      const response = await axios.post('http://localhost:5000/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred while analyzing the image');
    } finally {
      setLoading(false);
    }
  };

  const renderDetectedLabels = () => {
    if (!result || !result.detected_labels) return null;
    return (
      <div className="detected-section">
        <h4>Detected Materials & Features</h4>
        <ul className="labels-list">
          {result.detected_labels.map((label, idx) => (
            <li key={idx}>
              <span className="label-name">{label.description}</span>
              <span className="confidence">
                {(label.confidence * 100).toFixed(1)}% confidence
              </span>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  const renderDetectedObjects = () => {
    if (!result || !result.detected_objects || result.detected_objects.length === 0)
      return null;
    return (
      <div className="detected-section">
        <h4>Identified Objects</h4>
        <ul className="objects-list">
          {result.detected_objects.map((obj, idx) => (
            <li key={idx}>
              <span className="object-name">{obj.name}</span>
              <span className="confidence">
                {(obj.confidence * 100).toFixed(1)}%
              </span>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="studio-container">
      <header className="studio-header">
        <h1>🏗️ Civil Engineering Insight Studio</h1>
        <p>AI-Powered Structural Analysis & Documentation</p>
      </header>

      <main className="studio-main">
        <div className="input-section">
          <form onSubmit={handleSubmit} className="analysis-form">
            <div className="form-group">
              <label htmlFor="image-input">Upload Image</label>
              <input
                id="image-input"
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="file-input"
              />
              {imagePreview && (
                <div className="image-preview">
                  <img src={imagePreview} alt="Preview" />
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="scenario-select">Select Analysis Scenario</label>
              <select
                id="scenario-select"
                value={scenario}
                onChange={handleScenarioChange}
                className="scenario-select"
              >
                {scenarios.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <p className="scenario-description">
                {scenario === 'Material Identification' &&
                  'Identify and analyze construction materials in the structure'}
                {scenario === 'Project Documentation' &&
                  'Document construction progress and structural elements'}
                {scenario === 'Structural Analysis' &&
                  'Analyze structural components and engineering features'}
              </p>
            </div>

            <button
              type="submit"
              className="submit-btn"
              disabled={loading || !image}
            >
              {loading ? 'Analyzing...' : 'Analyze Structure'}
            </button>
          </form>
        </div>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <div className="results-section">
            <div className="tabs">
              <button
                className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
                onClick={() => setActiveTab('analysis')}
              >
                AI Analysis
              </button>
              <button
                className={`tab ${activeTab === 'detection' ? 'active' : ''}`}
                onClick={() => setActiveTab('detection')}
              >
                Detections
              </button>
            </div>

            {activeTab === 'analysis' && (
              <div className="analysis-content">
                <h3>Scenario: {result.scenario}</h3>
                <div className="ai-analysis">
                  <h4>Detailed Analysis</h4>
                  <p>{result.ai_analysis}</p>
                </div>
              </div>
            )}

            {activeTab === 'detection' && (
              <div className="detection-content">
                {renderDetectedLabels()}
                {renderDetectedObjects()}
                {result.detected_text && result.detected_text.length > 0 && (
                  <div className="detected-section">
                    <h4>Detected Text</h4>
                    <p>{result.detected_text.join(' | ')}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default CivilEngineeringStudio;