<p align="center">
    <img src="./assets/logo.webp" alt="Lavender Data Logo" width="50%" />
</p>

<h2>
    <p align="center">
        Load & evolve datasets efficiently
    </p>
</h2>

<p align="center">
    <a href="https://docs.lavenderdata.com/">
        <img alt="Docs" src="https://img.shields.io/badge/Docs-docs.svg">
    </a>
    <a href="https://discord.gg/fal-ai">
        <img alt="Discord" src="https://img.shields.io/badge/Discord-chat-2eb67d.svg?logo=discord">
    </a>
    <a href="https://github.com/fal-ai/lavender-data/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-green.svg">
    </a>
</p>

<br />

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
    <article style="border: 1px solid #ccc; padding: 1rem; border-radius: 0.5rem;">
        <p style="display: flex; align-items: center; gap: 0.5rem;">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="--sl-icon-size: 1.333em;"><path d="M22 9.67a1 1 0 0 0-.86-.67l-5.69-.83L12.9 3a1 1 0 0 0-1.8 0L8.55 8.16 2.86 9a1 1 0 0 0-.81.68 1 1 0 0 0 .25 1l4.13 4-1 5.68a1 1 0 0 0 1.45 1.07L12 18.76l5.1 2.68c.14.08.3.12.46.12a1 1 0 0 0 .99-1.19l-1-5.68 4.13-4A1 1 0 0 0 22 9.67Zm-6.15 4a1 1 0 0 0-.29.89l.72 4.19-3.76-2a1 1 0 0 0-.94 0l-3.76 2 .72-4.19a1 1 0 0 0-.29-.89l-3-3 4.21-.61a1 1 0 0 0 .76-.55L12 5.7l1.88 3.82a1 1 0 0 0 .76.55l4.21.61-3 2.99Z"></path></svg>
            <span>Remote Preprocessing</span>
        </p>
        <div>
            <ul>
                <li>Preprocess data on a remote server and offload your training GPUs</li>
                <li>Load data directly into memory through a network without any disk usage</li>
                <li>Support cloud storages</li>
            </ul>
        </div>
    </article>
    <article style="border: 1px solid #ccc; padding: 1rem; border-radius: 0.5rem;">
        <p style="display: flex; align-items: center; gap: 0.5rem;">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="--sl-icon-size: 1.333em;"><path d="M8.7 10a1 1 0 0 0 1.41 0 1 1 0 0 0 0-1.41l-6.27-6.3a1 1 0 0 0-1.42 1.42ZM21 14a1 1 0 0 0-1 1v3.59L15.44 14A1 1 0 0 0 14 15.44L18.59 20H15a1 1 0 0 0 0 2h6a1 1 0 0 0 .38-.08 1 1 0 0 0 .54-.54A1 1 0 0 0 22 21v-6a1 1 0 0 0-1-1Zm.92-11.38a1 1 0 0 0-.54-.54A1 1 0 0 0 21 2h-6a1 1 0 0 0 0 2h3.59L2.29 20.29a1 1 0 0 0 0 1.42 1 1 0 0 0 1.42 0L20 5.41V9a1 1 0 0 0 2 0V3a1 1 0 0 0-.08-.38Z"></path></svg>
            <span>Joinable Dataset</span>
        </p>
        <div>
            <ul>
                <li>Add new features to your dataset without rewriting your data</li>
                <li>Selectively load only the features you need for your task</li>
            </ul>
        </div>
    </article>
    <article style="border: 1px solid #ccc; padding: 1rem; border-radius: 0.5rem;">
        <p style="display: flex; align-items: center; gap: 0.5rem;">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="--sl-icon-size: 1.333em;"><path fill-rule="evenodd" d="M1.44 8.855v-.001l3.527-3.516c.34-.344.802-.541 1.285-.548h6.649l.947-.947c3.07-3.07 6.207-3.072 7.62-2.868a1.821 1.821 0 0 1 1.557 1.557c.204 1.413.203 4.55-2.868 7.62l-.946.946v6.649a1.845 1.845 0 0 1-.549 1.286l-3.516 3.528a1.844 1.844 0 0 1-3.11-.944l-.858-4.275-4.52-4.52-2.31-.463-1.964-.394A1.847 1.847 0 0 1 .98 10.693a1.843 1.843 0 0 1 .46-1.838Zm5.379 2.017-3.873-.776L6.32 6.733h4.638l-4.14 4.14Zm8.403-5.655c2.459-2.46 4.856-2.463 5.89-2.33.134 1.035.13 3.432-2.329 5.891l-6.71 6.71-3.561-3.56 6.71-6.711Zm-1.318 15.837-.776-3.873 4.14-4.14v4.639l-3.364 3.374Z" clip-rule="evenodd"></path><path d="M9.318 18.345a.972.972 0 0 0-1.86-.561c-.482 1.435-1.687 2.204-2.934 2.619a8.22 8.22 0 0 1-1.23.302c.062-.365.157-.79.303-1.229.415-1.247 1.184-2.452 2.62-2.935a.971.971 0 1 0-.62-1.842c-.12.04-.236.084-.35.13-2.02.828-3.012 2.588-3.493 4.033a10.383 10.383 0 0 0-.51 2.845l-.001.016v.063c0 .536.434.972.97.972H2.24a7.21 7.21 0 0 0 .878-.065c.527-.063 1.248-.19 2.02-.447 1.445-.48 3.205-1.472 4.033-3.494a5.828 5.828 0 0 0 .147-.407Z"></path></svg>
            <span>Dynamic Data Loading</span> 
        </p>
        <div>
            <ul>
                <li>Filter rows/columns on the fly</li>
                <li>Resume an iteration from where you left off</li>
                <li>Retry or skip failed samples to make it fault tolerant</li>
                <li>Shuffle data across shards</li>
            </ul>
        </div>
    </article>
    <article style="border: 1px solid #ccc; padding: 1rem; border-radius: 0.5rem;">
        <p style="display: flex; align-items: center; gap: 0.5rem;">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="--sl-icon-size: 1.333em;"><path d="M21 14h-1V7a3 3 0 0 0-3-3H7a3 3 0 0 0-3 3v7H3a1 1 0 0 0-1 1v2a3 3 0 0 0 3 3h14a3 3 0 0 0 3-3v-2a1 1 0 0 0-1-1ZM6 7a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v7H6V7Zm14 10a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-1h16v1Z"></path></svg>
            <span>Web UI</span>
        </p>
        <div>
            <ul>
                <li>Define and preview your datasets</li>
                <li>Track the realtime progress of your iterations</li>
            </ul>
        </div>
    </article>
</div>

### Why Lavender Data?

Traditional ML data pipelines often face several challenges:

- **GPU Memory Overhead**: Preprocessing on the same GPU used for training
- **Disk Space Limitations**: Having to store entire datasets on disk
- **Inflexible Data Management**: Difficulty in adding new features or columns
- **Poor Fault Tolerance**: Failing when a single sample errors out

Lavender Data solves these problems by providing a flexible, efficient, and robust solution for ML data management and preprocessing.

Ready to get started? Check out our [Quick Start Guide](https://docs.lavenderdata.com/quick-start) to begin using Lavender Data in your ML workflow.
