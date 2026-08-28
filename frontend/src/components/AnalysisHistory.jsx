import React, { useState, useEffect } from 'react';
import { History, Search, Filter, Trash2, Eye, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function AnalysisHistory({ onSelectRecord }) {
  const [history, setHistory] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [labelFilter, setLabelFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const data = await api.getAnalyses(page, 8, labelFilter || null, searchQuery || null);
      setHistory(data.data || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, labelFilter, searchQuery]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this analysis record?")) {
      try {
        await api.deleteAnalysis(id);
        fetchHistory();
      } catch (err) {
        alert("Failed to delete record.");
      }
    }
  };

  const totalPages = Math.ceil(total / 8) || 1;

  const getLabelPill = (lbl) => {
    switch (lbl?.toUpperCase()) {
      case 'ACCEPTABLE':
        return <span className="badge-acceptable" style={{ padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700 }}>ACCEPTABLE</span>;
      case 'DEGRADED':
        return <span className="badge-degraded" style={{ padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700 }}>DEGRADED</span>;
      case 'DEFECTIVE':
      default:
        return <span className="badge-defective" style={{ padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700 }}>DEFECTIVE</span>;
    }
  };

  return (
    <div className="glass-card" style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <History size={20} color="var(--primary)" /> Analysis History Log ({total})
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Persistent audit log stored in SQLite database</p>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Search Box */}
          <div style={{ position: 'relative', minWidth: '200px' }}>
            <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: 10, top: 10 }} />
            <input
              type="text"
              placeholder="Search filename..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              style={{
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '0.45rem 0.5rem 0.45rem 2.2rem',
                color: 'white',
                fontSize: '0.85rem',
                width: '100%'
              }}
            />
          </div>

          {/* Label Filter dropdown */}
          <div style={{ position: 'relative' }}>
            <select
              value={labelFilter}
              onChange={(e) => { setLabelFilter(e.target.value); setPage(1); }}
              style={{
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '0.45rem 1rem',
                color: 'white',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <option value="">All Quality Statuses</option>
              <option value="ACCEPTABLE">Acceptable</option>
              <option value="DEGRADED">Degraded</option>
              <option value="DEFECTIVE">Defective</option>
            </select>
          </div>

          <button onClick={fetchHistory} className="btn-secondary" style={{ padding: '0.45rem' }}>
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* History Data Table */}
      <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Preview</th>
              <th style={{ padding: '0.75rem 1rem' }}>Filename</th>
              <th style={{ padding: '0.75rem 1rem' }}>Quality Score</th>
              <th style={{ padding: '0.75rem 1rem' }}>Status Label</th>
              <th style={{ padding: '0.75rem 1rem' }}>Issues</th>
              <th style={{ padding: '0.75rem 1rem' }}>Timestamp</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan="7" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Loading history records...
                </td>
              </tr>
            ) : history.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No analysis history found. Upload images to generate records.
                </td>
              </tr>
            ) : (
              history.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => onSelectRecord(item)}
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    cursor: 'pointer',
                    transition: 'background 0.15s ease'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.04)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '0.6rem 1rem' }}>
                    <img src={item.image_url} alt="Thumbnail" style={{ width: 44, height: 44, objectFit: 'cover', borderRadius: '6px', border: '1px solid var(--border-color)' }} />
                  </td>
                  <td style={{ padding: '0.6rem 1rem', fontWeight: 600 }}>
                    {item.original_filename}
                    <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 400 }}>
                      {item.width}x{item.height} • {Math.round(item.file_size / 1024)} KB
                    </span>
                  </td>
                  <td style={{ padding: '0.6rem 1rem' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.95rem' }}>{item.quality_score}</span> / 100
                  </td>
                  <td style={{ padding: '0.6rem 1rem' }}>
                    {getLabelPill(item.quality_label)}
                  </td>
                  <td style={{ padding: '0.6rem 1rem', color: 'var(--text-muted)' }}>
                    {item.issues?.length > 0 ? (
                      <span style={{ color: '#fbbf24', fontSize: '0.8rem' }}>{item.issues.map(i => i.type).join(', ')}</span>
                    ) : (
                      <span style={{ color: '#34d399', fontSize: '0.8rem' }}>None</span>
                    )}
                  </td>
                  <td style={{ padding: '0.6rem 1rem', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '0.6rem 1rem', textAlign: 'right' }}>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.4rem' }}>
                      <button onClick={(e) => { e.stopPropagation(); onSelectRecord(item); }} className="btn-secondary" style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}>
                        <Eye size={14} /> View
                      </button>
                      <button onClick={(e) => handleDelete(item.id, e)} className="btn-secondary" style={{ padding: '0.35rem 0.6rem', color: '#f43f5e', borderColor: 'rgba(244, 63, 94, 0.3)' }}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Showing Page {page} of {totalPages} ({total} total records)
        </span>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="btn-secondary"
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
          >
            <ChevronLeft size={16} /> Previous
          </button>

          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="btn-secondary"
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      </div>

    </div>
  );
}
