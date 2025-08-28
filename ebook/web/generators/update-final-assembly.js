#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

// Paths
const bookPath = path.join(__dirname, '..', 'en', 'book.html');
const templatePath = path.join(__dirname, '..', 'en', 'core-philosophy-architecture', 'ai-recruiter-dynamic-team', 'index.html');
const targetDir = path.join(__dirname, '..', 'en', 'execution-quality', 'final-assembly-last-mile');
const targetPath = path.join(targetDir, 'index.html');

// Read files
const book = fs.readFileSync(bookPath, 'utf8');
const template = fs.readFileSync(templatePath, 'utf8');

// Extract chapter 13 content from book.html
const startMarker = '<h2 class="chapter-title">Chapter 13:';
const endMarker = '<h2 class="chapter-title">Chapter 14:';
const startIdx = book.indexOf(startMarker);
if (startIdx < 0) throw new Error('Start of Chapter 13 not found in book.html');
const endIdx = book.indexOf(endMarker, startIdx);
if (endIdx < 0) throw new Error('End of Chapter 13 not found in book.html');
const chapterHtml = book.slice(startIdx, endIdx);

// Split template at chapter-content
const splitTag = '<div class="chapter-content">';
const [tmplHead, tmplRest] = template.split(splitTag);
if (!tmplRest) throw new Error('chapter-content container not found in template');
// Keep the opening div tag in head
const beforeContent = tmplHead + splitTag;
// Find closing tag before nav or script
const closing = '</div>'; // closes chapter-content
// We will append closing div and the rest after closing div of content
// Find the position of closing div that matches the opening
const restSplit = tmplRest.split(closing);
if (restSplit.length < 2) throw new Error('Closing chapter-content </div> not found in template');
const afterContent = restSplit.slice(1).join(closing);

// Compose final output
const output = beforeContent + '\n' + chapterHtml + '\n' + closing + afterContent;

// Ensure target directory exists
fs.mkdirSync(targetDir, { recursive: true });
fs.writeFileSync(targetPath, output, 'utf8');
console.log('Updated', targetPath);
