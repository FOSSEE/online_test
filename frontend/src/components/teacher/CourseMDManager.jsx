import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { FaDownload, FaUpload, FaFileArchive, FaInfoCircle } from 'react-icons/fa';
import { downloadCourseMD, uploadCourseMD } from '../../api/api';

const CourseMDManager = () => {
    const { courseId } = useParams();
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate file extension
            const fileExtension = file.name.split('.').pop().toLowerCase();
            if (fileExtension !== 'zip') {
                setMessage({
                    type: 'error',
                    text: 'Please select a ZIP file'
                });
                setSelectedFile(null);
                e.target.value = ''; // Reset file input
                return;
            }
            setSelectedFile(file);
            setMessage({ type: '', text: '' });
        }
    };

    const handleDownload = async () => {
        if (!courseId) return;

        setDownloading(true);
        setMessage({ type: '', text: '' });

        try {
            await downloadCourseMD(courseId);
            setMessage({
                type: 'success',
                text: 'Course structure downloaded successfully!'
            });
        } catch (error) {
            const errorMessage = error.response?.data?.error || 'Failed to download course structure';
            setMessage({
                type: 'error',
                text: errorMessage
            });
        } finally {
            setDownloading(false);
        }
    };

    const handleUpload = async () => {
        if (!courseId || !selectedFile) {
            setMessage({
                type: 'error',
                text: 'Please select a ZIP file to upload'
            });
            return;
        }

        setUploading(true);
        setMessage({ type: '', text: '' });

        try {
            const response = await uploadCourseMD(courseId, selectedFile);
            setMessage({
                type: 'success',
                text: response.message || 'Course structure uploaded successfully!'
            });
            setSelectedFile(null);
            // Reset file input
            const fileInput = document.querySelector('input[type="file"]');
            if (fileInput) fileInput.value = '';

            // Reload page after 2 seconds to reflect changes
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (error) {
            const errorMessage = error.response?.data?.error || 'Failed to upload course structure';
            setMessage({
                type: 'error',
                text: errorMessage
            });
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/15 border-2 border-cyan-500/30 flex items-center justify-center ">
                    <FaFileArchive className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                    <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">Upload / Download MD</h3>
                    <p className="text-xs muted">Export or import your course structure as Markdown</p>
                </div>
            </div>

            {/* Info Box */}
            <div className="bg-blue-500/20  border-2 border-blue-500/40 dark:border-blue-500/30 rounded-lg p-4 flex items-start gap-3">
                <FaInfoCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-300">
                    <p className="font-medium mb-1 text-sm text-blue-700 dark:text-blue-400">About Course MD Files:</p>
                    <ul className="list-disc list-inside space-y-1 text-xs text-blue-600 dark:text-blue-400/80">
                        <li>Download exports your entire course structure (modules, lessons, quizzes) as a ZIP file</li>
                        <li>Upload accepts a ZIP file containing Markdown course files</li>
                        <li>Files must include a valid <code className="bg-black/20 px-1 rounded">toc.yml</code> file</li>
                        <li>Useful for backup, migration, or bulk editing course content</li>
                    </ul>
                </div>
            </div>

            {/* Download Section */}
            <div className="card-strong p-6 border-2 border-[var(--border-strong)] shadow-lg rounded-2xl bg-[var(--surface)]">
                <div className="flex items-center gap-3 mb-4">
                    <FaDownload className="w-5 h-5 text-green-400" />
                    <h3 className="text-lg font-semibold">Download Course Structure</h3>
                </div>
                <p className="text-sm text-[var(--text-secondary)] mb-4">
                    Export your course structure as a ZIP file containing all modules, lessons, and quizzes in Markdown format.
                </p>
                <button
                    onClick={handleDownload}
                    disabled={downloading}
                    className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 text-white shadow-lg shadow-green-500/20 px-6 py-2.5 rounded-xl font-bold transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {downloading ? (
                        <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Downloading...</span>
                        </>
                    ) : (
                        <>
                            <FaDownload className="w-4 h-4" />
                            <span>Download MD</span>
                        </>
                    )}
                </button>
            </div>

            {/* Upload Section */}
            <div className="card-strong p-6 border-2 border-[var(--border-strong)] shadow-lg rounded-2xl bg-[var(--surface)]">
                <div className="flex items-center gap-3 mb-4">
                    <FaUpload className="w-5 h-5 text-blue-400" />
                    <h3 className="text-lg font-semibold">Upload Course Structure</h3>
                </div>
                <p className="text-sm text-[var(--text-secondary)] mb-4">
                    Import a course structure from a ZIP file. The file must contain valid Markdown files and a <code className="bg-black/20 px-1 rounded">toc.yml</code> file.
                </p>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">
                            Select ZIP File
                        </label>
                        <div className="flex items-center gap-3">
                            <label className="flex-1 cursor-pointer">
                                <input
                                    type="file"
                                    accept=".zip"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />
                                <div className="border border-[var(--border-color)] rounded-lg p-3 bg-[var(--input-bg)] hover:bg-[var(--border-subtle)] transition flex items-center gap-3">
                                    <FaFileArchive className="w-5 h-5 text-[var(--text-secondary)]" />
                                    <span className="text-sm text-[var(--text-secondary)]">
                                        {selectedFile ? selectedFile.name : 'Choose file'}
                                    </span>
                                </div>
                            </label>
                        </div>
                        {selectedFile && (
                            <p className="text-xs text-green-400 mt-2 flex items-center gap-1">
                                <FaFileArchive className="w-3 h-3" />
                                {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                            </p>
                        )}
                    </div>

                    <button
                        onClick={handleUpload}
                        disabled={uploading || !selectedFile}
                        className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white shadow-lg shadow-blue-500/20 px-6 py-2.5 rounded-xl font-bold transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {uploading ? (
                            <>
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                <span>Uploading...</span>
                            </>
                        ) : (
                            <>
                                <FaUpload className="w-4 h-4" />
                                <span>Upload MD</span>
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Message Display */}
            {message.text && (
                <div className={`rounded-lg p-4 ${message.type === 'success'
                    ? 'bg-green-500/10 border border-green-500/30 text-green-300'
                    : 'bg-red-500/10 border border-red-500/30 text-red-300'
                    }`}>
                    {message.text}
                </div>
            )}
        </div>
    );
};

export default CourseMDManager;




