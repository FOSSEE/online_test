import React, { useEffect, useState } from 'react';
import useGradingSystemStore from '../../store/teacherGradeStore';

export default function GradingSystemsList({ onAdd, onManage }) {
  const { gradingSystems, loadGradingSystems, loading, error } = useGradingSystemStore();

  useEffect(() => { loadGradingSystems(); }, []);

  return (
    <div className="card-strong p-6 min-h-[400px]">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">Grading Systems</h2>
        <button className="btn btn-primary" onClick={onAdd}>Add Grading System</button>
      </div>
      {loading && <div>Loading...</div>}
      {error && <div className="text-red-500">{error}</div>}
      <div className="space-y-4">
        {gradingSystems.length > 0 ? (
          gradingSystems.map(gs => (
            <div key={gs.id} className="card p-4 flex flex-col md:flex-row md:items-center justify-between">
              <div>
                <h3 className="font-semibold text-lg">{gs.name}</h3>
                <p className="text-sm muted">{gs.description}</p>
              </div>
              <div className="flex gap-2 mt-2 md:mt-0">
                <button className="btn btn-secondary" onClick={() => onManage(gs)}>Manage</button>
                {/* Add delete/edit here if needed */}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-muted">No grading systems found.</div>
        )}
      </div>
    </div>
  );
}