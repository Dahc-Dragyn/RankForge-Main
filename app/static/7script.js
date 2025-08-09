// File: static/script.js
// Author: MCP Development Core
// Description: Frontend logic for user authentication and API interaction.

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. DOM Element Selection ---
    const authContainer = document.getElementById('auth-container');
    const dashboardContainer = document.getElementById('dashboard-container');
    const loginForm = document.getElementById('login-form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const googleLoginButton = document.getElementById('google-login-button');
    const logoutButton = document.getElementById('logout-button');
    const authError = document.getElementById('auth-error');
    const welcomeMessage = document.getElementById('welcome-message');
    const analysisForm = document.getElementById('analysis-form');
    const nicheInput = document.getElementById('niche');
    const locationInput = document.getElementById('location');
    const resultsContainer = document.getElementById('results-container');
    const assetStatus = document.getElementById('asset-status');
    const assetList = document.getElementById('asset-list');
    const settingsForm = document.getElementById('settings-form');
    const netlifyApiKeyInput = document.getElementById('netlify-api-key');
    const settingsStatus = document.getElementById('settings-status');
    const editorModal = document.getElementById('editor-modal');
    const editorTabs = document.getElementById('editor-tabs');
    const contentEditorTextarea = document.getElementById('content-editor-textarea');
    const finalizeDeployBtn = document.getElementById('finalize-deploy-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');

    // --- 2. State Management ---
    let currentIdToken = null;
    let editorState = {};

    // --- 3. Firebase Initialization ---
    const firebaseConfig = {
        apiKey: "AIzaSyD4GgWSuLeS_M_jqnmV-TGtMp7aiD9_wq8",
        authDomain: "local-arbitrage-mcp.firebaseapp.com",
        projectId: "local-arbitrage-mcp",
        storageBucket: "local-arbitrage-mcp.firebasestorage.app",
        messagingSenderId: "256860285282",
        appId: "1:256860285282:web:28dce1c9541391c0e2e43b",
        measurementId: "G-3DZXLM7D8F"
    };
    const app = firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();

    // --- 4. Core Application Logic ---
    auth.onAuthStateChanged(user => {
        if (user) {
            dashboardContainer.classList.remove('hidden');
            authContainer.classList.add('hidden');
            welcomeMessage.textContent = `Welcome, ${user.email}`;
            user.getIdToken().then(token => {
                currentIdToken = token;
                loadUserSettings();
                loadUserSites();
            });
        } else {
            dashboardContainer.classList.add('hidden');
            authContainer.classList.remove('hidden');
            currentIdToken = null;
        }
    });

    // --- Event Listeners ---
    loginForm.addEventListener('submit', handleEmailLogin);
    googleLoginButton.addEventListener('click', handleGoogleLogin);
    logoutButton.addEventListener('click', () => auth.signOut());
    settingsForm.addEventListener('submit', handleSaveSettings);
    analysisForm.addEventListener('submit', handleAnalysis);
    document.addEventListener('click', handleDynamicClicks);
    cancelEditBtn.addEventListener('click', closeContentEditor);
    finalizeDeployBtn.addEventListener('click', handleFinalizeDeploy);
    editorTabs.addEventListener('click', handleTabClick);

    // --- Functions ---
    function handleEmailLogin(e) {
        e.preventDefault();
        const email = emailInput.value;
        const password = passwordInput.value;
        authError.textContent = '';
        auth.signInWithEmailAndPassword(email, password)
            .catch(error => {
                if (error.code === 'auth/user-not-found') {
                    auth.createUserWithEmailAndPassword(email, password)
                        .catch(err => { authError.textContent = err.message; });
                } else {
                    authError.textContent = error.message;
                }
            });
    }

    function handleGoogleLogin() {
        const provider = new firebase.auth.GoogleAuthProvider();
        authError.textContent = '';
        auth.signInWithPopup(provider)
            .catch(error => { authError.textContent = error.message; });
    }

    async function handleSaveSettings(e) {
        e.preventDefault();
        const apiKey = netlifyApiKeyInput.value;
        if (!apiKey || !currentIdToken) return;
        settingsStatus.textContent = 'Saving...';
        try {
            const response = await fetch('/api/v1/user/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentIdToken}` },
                body: JSON.stringify({ netlify_api_key: apiKey })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to save.');
            settingsStatus.textContent = 'Settings saved successfully!';
        } catch (error) {
            settingsStatus.textContent = `Error: ${error.message}`;
        }
        setTimeout(() => { settingsStatus.textContent = ''; }, 3000);
    }

    async function loadUserSettings() {
        if (!currentIdToken) return;
        try {
            const response = await fetch('/api/v1/user/settings', {
                headers: { 'Authorization': `Bearer ${currentIdToken}` }
            });
            const data = await response.json();
            if (response.ok && data.netlify_api_key) {
                netlifyApiKeyInput.value = data.netlify_api_key;
            }
        } catch (error) {
            console.error("Could not load user settings:", error);
        }
    }

    async function handleAnalysis(e) {
        e.preventDefault();
        if (!currentIdToken) return;
        const niche = nicheInput.value;
        const location = locationInput.value;
        resultsContainer.innerHTML = `<p>Analyzing opportunity for "${niche}" in "${location}"...</p>`;
        try {
            const response = await fetch('/api/v1/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentIdToken}` },
                body: JSON.stringify({ niche, location })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'An unknown error occurred.');
            renderAnalysisResults(data);
        } catch (error) {
            resultsContainer.innerHTML = `<p class="error-message">Failed to get analysis: ${error.message}</p>`;
        }
    }

    function renderAnalysisResults(data) {
        if (data.error) {
            resultsContainer.innerHTML = `<p class="error-message">Analysis Error: ${data.error}</p>`;
            return;
        }
        let html = `<h3>Analysis for "${data.niche}" in "${data.location}"</h3>
            <p><strong>Opportunity Score:</strong> ${data.opportunity_score || 'N/A'} / 100</p>
            <p><strong>Justification:</strong> ${data.justification || 'N/A'}</p>
            <button class="generate-content-btn" data-niche="${data.niche}" data-location="${data.location}">
                Generate Content & Edit
            </button>`;
        resultsContainer.innerHTML = html;
    }
    
    async function loadUserSites() {
        if (!currentIdToken) return;
        assetList.innerHTML = '<li>Loading sites...</li>';
        try {
            const response = await fetch('/api/v1/sites', {
                headers: { 'Authorization': `Bearer ${currentIdToken}` }
            });
            const sites = await response.json();
            if (!response.ok) throw new Error(sites.detail || 'Failed to load sites.');
            renderUserSites(sites);
        } catch (error) {
            assetList.innerHTML = `<li class="error-message">${error.message}</li>`;
        }
    }

    function renderUserSites(sites) {
        if (sites.length === 0) {
            assetList.innerHTML = '<li>No content found in CMS. Generate some above!</li>';
            return;
        }
        let html = '';
        sites.forEach(site => {
            // *** THIS IS THE FIX ***
            // Use 'sanity_site_id' which is now provided by the backend.
            // Removed the non-functional "View Live" link for now.
            html += `
                <li class="site-item">
                    <div>
                        <strong>${site.business_name}</strong><br>
                        <small>${site.niche} in ${site.location}</small>
                    </div>
                    <div class="site-actions">
                        <button class="edit-site-btn" data-site-id="${site.sanity_site_id}">Edit Content</button>
                    </div>
                </li>
            `;
        });
        assetList.innerHTML = html;
    }

    function handleDynamicClicks(e) {
        if (e.target) {
            if (e.target.classList.contains('generate-content-btn')) {
                const niche = e.target.dataset.niche;
                const location = e.target.dataset.location;
                const businessName = prompt(`Enter a fictional business name for this asset:`, `Apex ${niche}`);
                if (businessName && businessName.trim() !== "") {
                    startContentGeneration(businessName, niche, location);
                }
            } else if (e.target.classList.contains('edit-site-btn')) {
                const siteId = e.target.dataset.siteId;
                handleEditSite(siteId);
            }
        }
    }

    async function handleEditSite(siteId) {
        assetStatus.innerHTML = `<p>Loading content for editing...</p>`;
        try {
            const response = await fetch(`/api/v1/sites/${siteId}`, {
                headers: { 'Authorization': `Bearer ${currentIdToken}` }
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to load site content.');
            
            // *** THIS IS THE FIX ***
            // Populate editor state with the correct 'sanity_site_id'.
            editorState = { 
                businessName: data.business_name,
                niche: data.niche,
                location: data.location,
                content: data.content,
                site_structure: data.site_structure,
                sanity_site_id: data.sanity_site_id 
            };
            
            openContentEditor();
            assetStatus.innerHTML = '';
        } catch (error) {
            assetStatus.innerHTML = `<p class="error-message">${error.message}</p>`;
        }
    }

    async function startContentGeneration(businessName, niche, location) {
        assetStatus.innerHTML = `<p>Generating initial content for "${businessName}"...</p>`;
        try {
            const response = await fetch('/api/v1/generate-content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentIdToken}` },
                body: JSON.stringify({ business_name: businessName, niche, location })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to generate content.');
            
            editorState = { businessName, niche, location, ...data };
            openContentEditor();
            assetStatus.innerHTML = `<p>Content generated. Please review in the editor.</p>`;
        } catch (error) {
            assetStatus.innerHTML = `<p class="error-message">Error generating content: ${error.message}</p>`;
        }
    }

    function openContentEditor() {
        editorTabs.innerHTML = '';
        const filenames = Object.keys(editorState.content);
        
        filenames.forEach((filename, index) => {
            const tab = document.createElement('div');
            tab.className = 'tab';
            tab.textContent = pageNameFromFilename(filename);
            tab.dataset.filename = filename;
            if (index === 0) {
                tab.classList.add('active');
                contentEditorTextarea.value = editorState.content[filename];
            }
            editorTabs.appendChild(tab);
        });
        
        document.body.classList.add('modal-open');
        editorModal.classList.remove('hidden');
    }

    function closeContentEditor() {
        document.body.classList.remove('modal-open');
        editorModal.classList.add('hidden');
    }

    function handleTabClick(e) {
        if (e.target && e.target.classList.contains('tab')) {
            const activeTab = editorTabs.querySelector('.tab.active');
            if (activeTab) {
                editorState.content[activeTab.dataset.filename] = contentEditorTextarea.value;
            }
            
            editorTabs.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            e.target.classList.add('active');
            contentEditorTextarea.value = editorState.content[e.target.dataset.filename];
        }
    }

    async function handleFinalizeDeploy() {
        const activeTab = editorTabs.querySelector('.tab.active');
        if (activeTab) {
            editorState.content[activeTab.dataset.filename] = contentEditorTextarea.value;
        }
        closeContentEditor();
        assetStatus.innerHTML = `<p>Pushing content to CMS for "${editorState.businessName}"...</p>`;
        try {
            const response = await fetch('/api/v1/assemble-and-deploy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentIdToken}` },
                body: JSON.stringify({
                    business_name: editorState.businessName,
                    niche: editorState.niche,
                    location: editorState.location,
                    edited_content: editorState.content,
                    site_structure: editorState.site_structure
                    // No need to send site_id here, backend handles it
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to start task.');
            
            assetStatus.innerHTML = `<p>CMS push for "${editorState.businessName}" is in progress. Task ID: ${data.task_id}</p>`;
            pollDeploymentStatus(data.task_id, editorState.businessName);
        } catch (error) {
            assetStatus.innerHTML = `<p class="error-message">Error starting task: ${error.message}</p>`;
        }
    }

    function pollDeploymentStatus(taskId, businessName) {
        const intervalId = setInterval(async () => {
            try {
                const response = await fetch(`/api/v1/deployment-status/${taskId}`, {
                    headers: { 'Authorization': `Bearer ${currentIdToken}` }
                });
                if (!response.ok) { clearInterval(intervalId); return; }
                const data = await response.json();
                if (data.status === 'complete') {
                    clearInterval(intervalId);
                    const result = data.result;
                    let resultHTML = `<p><strong>Success!</strong> Content for "${businessName}" pushed to CMS.</p>`;
                    if (result.sanity_result && result.sanity_result.error) {
                        resultHTML += `<p class="error-message"><strong>CMS Error:</strong> ${result.sanity_result.error}</p>`;
                    }
                    assetStatus.innerHTML = resultHTML;
                    loadUserSites();
                } else if (data.status === 'failed') {
                    clearInterval(intervalId);
                    assetStatus.innerHTML = `<p class="error-message"><strong>Failed!</strong> Task for "${businessName}" failed: ${data.error}</p>`;
                }
            } catch (error) {
                clearInterval(intervalId);
            }
        }, 5000);
    }

    function pageNameFromFilename(filename) { return filename.split('.')[0].replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()); }
});
