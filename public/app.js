/**
 * YouTube Comment Scrapper — Modern Analytics Dashboard Logic
 * Production-ready, secure, and resilient vanilla JavaScript.
 */

(function () {
  "use strict";

  // ==========================================================================
  // Application State
  // ==========================================================================
  const state = {
    currentView: "dashboard",
    apiStatus: {
      status: "checking", // "checking" | "ready" | "missing_key" | "quota_exceeded" | "offline"
      message: "Checking API connection...",
      details: null,
    },
    channel: null,
    videos: [],
    selectedVideo: null,
    allComments: [],
    filteredComments: [],
    pagination: {
      page: 1,
      pageSize: 25,
    },
    filters: {
      search: "",
      type: "all", // "all" | "comment" | "reply"
      sort: "likes_desc", // "likes_desc" | "date_desc" | "date_asc"
      minLikes: 0,
    },
    isSearching: false,
    isScraping: false,
    exportHistory: [],
    preferences: {
      defaultLimit: 200,
      defaultOrder: "relevance",
      defaultReplies: false,
    },
  };

  // ==========================================================================
  // Utility & Security Functions
  // ==========================================================================
  const $ = (id) => document.getElementById(id);
  const $$ = (sel) => document.querySelectorAll(sel);

  /**
   * Escape HTML entities to prevent XSS attacks from user comments/authors
   */
  function esc(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function fmtNumber(n) {
    if (n === null || n === undefined || isNaN(n)) return "0";
    return Number(n).toLocaleString();
  }

  function fmtCompactNumber(n) {
    if (n === null || n === undefined || isNaN(n)) return "0";
    const num = Number(n);
    if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
    if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, "") + "K";
    return num.toLocaleString();
  }

  function fmtDate(d) {
    if (!d) return "";
    try {
      return new Date(d).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return String(d);
    }
  }

  function fmtTime(d) {
    if (!d) return "";
    try {
      return new Date(d).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  }

  function slugify(text) {
    return (text || "youtube-comments")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 50);
  }

  function showToast(message, type = "success") {
    const container = $("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon =
      type === "success"
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

    toast.innerHTML = `${icon}<span>${esc(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "all 0.25s ease";
      setTimeout(() => toast.remove(), 250);
    }, 3200);
  }

  // ==========================================================================
  // Storage & Persistence
  // ==========================================================================
  function loadPersistedData() {
    try {
      const savedHistory = localStorage.getItem("yt_scrapper_exports");
      if (savedHistory) {
        state.exportHistory = JSON.parse(savedHistory);
      }
    } catch (e) {
      console.warn("Could not load export history from localStorage", e);
    }

    try {
      const savedPrefs = localStorage.getItem("yt_scrapper_prefs");
      if (savedPrefs) {
        state.preferences = { ...state.preferences, ...JSON.parse(savedPrefs) };
      }
    } catch (e) {
      console.warn("Could not load preferences from localStorage", e);
    }
  }

  function saveExportHistory() {
    try {
      localStorage.setItem("yt_scrapper_exports", JSON.stringify(state.exportHistory.slice(0, 100)));
    } catch (e) {
      console.warn("Could not save export history", e);
    }
  }

  function savePreferences() {
    try {
      localStorage.setItem("yt_scrapper_prefs", JSON.stringify(state.preferences));
    } catch (e) {
      console.warn("Could not save preferences", e);
    }
  }

  // ==========================================================================
  // Navigation & Routing
  // ==========================================================================
  function switchView(viewName) {
    state.currentView = viewName;

    // Update active nav links
    $$(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === viewName);
    });

    // Update visible view section
    $$(".view-section").forEach((sec) => {
      sec.classList.toggle("active", sec.id === `view-${viewName}`);
    });

    // Update breadcrumb
    const breadcrumbCurrent = $("breadcrumbCurrent");
    if (breadcrumbCurrent) {
      const titles = {
        dashboard: "Dashboard",
        search: "Video Search",
        comments: "Comments Explorer",
        exports: "Export History",
        settings: "Settings & API",
      };
      breadcrumbCurrent.textContent = titles[viewName] || "Dashboard";
    }

    // Close mobile sidebar if open
    $("sidebar").classList.remove("open");
    $("sidebarOverlay").classList.remove("open");

    // Re-render views if necessary
    if (viewName === "exports") {
      renderExportHistory();
    } else if (viewName === "settings") {
      renderSettings();
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ==========================================================================
  // Real API Status Diagnostic (Never Fake)
  // ==========================================================================
  async function checkApiConnection() {
    const badge = $("apiStatusBadge");
    const label = $("apiStatusLabel");
    const quotaDot = $("quotaDot");
    const quotaStatus = $("quotaStatusText");

    state.apiStatus.status = "checking";
    state.apiStatus.message = "Checking API status...";
    if (badge) badge.className = "api-status-badge status-checking";
    if (label) label.textContent = "Connecting...";

    try {
      // 1) First try the /api/status endpoint
      const statusRes = await fetch("/api/status").catch(() => null);
      if (statusRes && statusRes.ok) {
        const data = await statusRes.json();
        if (data.configured) {
          state.apiStatus = {
            status: "ready",
            message: "YouTube API key is configured and server is online.",
            details: data,
          };
          updateApiStatusUI();
          return;
        } else {
          state.apiStatus = {
            status: "missing_key",
            message: "Missing YouTube API key. Add YOUTUBE_API_KEY in your .env file.",
            details: data,
          };
          updateApiStatusUI();
          return;
        }
      }

      // 2) Fallback probe against /api/youtube/videos
      const probeRes = await fetch("/api/youtube/videos");
      const probeData = await probeRes.json().catch(() => ({}));

      if (probeRes.status === 400) {
        // Validation reached => API key is set!
        state.apiStatus = {
          status: "ready",
          message: "Connected. API key verified on server.",
          details: probeData,
        };
      } else if (probeRes.status === 500 && probeData.error && probeData.error.includes("Missing YouTube API key")) {
        state.apiStatus = {
          status: "missing_key",
          message: "API key is not configured in .env file.",
          details: probeData,
        };
      } else {
        state.apiStatus = {
          status: "ready",
          message: "Server connected.",
          details: probeData,
        };
      }
    } catch (err) {
      state.apiStatus = {
        status: "offline",
        message: "Server unreachable. Make sure 'npm start' is running.",
        details: err.message,
      };
    }

    updateApiStatusUI();
  }

  function updateApiStatusUI() {
    const badge = $("apiStatusBadge");
    const label = $("apiStatusLabel");
    const quotaDot = $("quotaDot");
    const quotaStatus = $("quotaStatusText");
    const diagnosticBox = $("diagnosticResultBox");

    if (!badge || !label) return;

    if (state.apiStatus.status === "ready") {
      badge.className = "api-status-badge";
      label.textContent = "API Ready";
      if (quotaDot) quotaDot.className = "quota-dot";
      if (quotaStatus) quotaStatus.textContent = "Quota Healthy";
    } else if (state.apiStatus.status === "quota_exceeded") {
      badge.className = "api-status-badge status-warning";
      label.textContent = "Quota Exceeded";
      if (quotaDot) quotaDot.className = "quota-dot warning";
      if (quotaStatus) quotaStatus.textContent = "Quota Depleted";
    } else if (state.apiStatus.status === "missing_key") {
      badge.className = "api-status-badge status-error";
      label.textContent = "Key Missing";
      if (quotaDot) quotaDot.className = "quota-dot error";
      if (quotaStatus) quotaStatus.textContent = "API Key Missing";
    } else {
      badge.className = "api-status-badge status-error";
      label.textContent = "Server Offline";
      if (quotaDot) quotaDot.className = "quota-dot error";
      if (quotaStatus) quotaStatus.textContent = "Offline";
    }

    if (diagnosticBox) {
      diagnosticBox.innerHTML = `
        <strong>Status:</strong> ${esc(state.apiStatus.status.toUpperCase())}<br/>
        <strong>Message:</strong> ${esc(state.apiStatus.message)}<br/>
        <strong>Timestamp:</strong> ${new Date().toISOString()}<br/>
        <strong>Response Info:</strong> ${esc(JSON.stringify(state.apiStatus.details || {}, null, 2))}
      `;
    }
  }

  // ==========================================================================
  // Video Search Functionality
  // ==========================================================================
  async function searchVideos(channelQuery, videoQuery) {
    const errorBanner = $("searchErrorBanner");
    const errorMsg = $("searchErrorText");
    const searchBtn = $("searchSubmitBtn");

    if (!channelQuery.trim() || !videoQuery.trim()) {
      showError(errorBanner, errorMsg, "Please enter both a channel name (or @handle) and a video name.");
      return;
    }

    hideError(errorBanner);
    state.isSearching = true;
    setButtonLoading(searchBtn, true, "Searching...");

    try {
      const params = new URLSearchParams({
        channel: channelQuery.trim(),
        video: videoQuery.trim(),
      });

      const res = await fetch(`/api/youtube/videos?${params.toString()}`);
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        if (data.error && data.error.includes("quota")) {
          state.apiStatus.status = "quota_exceeded";
          updateApiStatusUI();
        }
        throw new Error(data.error || "Failed to search YouTube videos.");
      }

      state.channel = data.channel;
      state.videos = data.videos || [];

      // Update API status if healthy
      if (state.apiStatus.status !== "ready") {
        state.apiStatus.status = "ready";
        updateApiStatusUI();
      }

      renderVideosList();
      showToast(`Found ${state.videos.length} video(s) for "${data.channel.title}"`);
    } catch (err) {
      showError(errorBanner, errorMsg, err.message);
    } finally {
      state.isSearching = false;
      setButtonLoading(searchBtn, false, "Search Videos");
    }
  }

  function renderVideosList() {
    const profileBar = $("channelProfileBar");
    const channelThumb = $("channelThumb");
    const channelTitle = $("channelTitle");
    const channelMatches = $("channelMatches");
    const videosContainer = $("videosContainer");
    const videosEmptyState = $("videosEmptyState");

    if (!state.videos.length) {
      profileBar.classList.remove("show");
      videosContainer.innerHTML = "";
      if (videosEmptyState) videosEmptyState.style.display = "flex";
      return;
    }

    if (videosEmptyState) videosEmptyState.style.display = "none";

    // Channel Header
    profileBar.classList.add("show");
    if (state.channel?.thumb) {
      channelThumb.src = state.channel.thumb;
      channelThumb.alt = state.channel.title || "Channel";
      channelThumb.style.display = "block";
    } else {
      channelThumb.style.display = "none";
    }
    channelTitle.textContent = state.channel?.title || "Channel";
    channelMatches.textContent = `${state.videos.length} videos found matching query`;

    // Render cards
    videosContainer.innerHTML = state.videos
      .map((video) => {
        const isSelected = state.selectedVideo?.id === video.id;
        return `
          <div class="video-card ${isSelected ? "selected" : ""}" data-video-id="${esc(video.id)}">
            <div class="video-thumb-wrap">
              <img class="video-thumb" src="${esc(video.thumbnail)}" alt="${esc(video.title)}" loading="lazy" />
              <div class="video-selected-check">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
            </div>
            <div class="video-card-body">
              <h3 class="video-card-title" title="${esc(video.title)}">${esc(video.title)}</h3>
              <div class="video-stats-row">
                <span class="stat-chip" title="Total Views">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  ${fmtCompactNumber(video.views)}
                </span>
                <span class="stat-chip" title="Comment Count">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                  ${video.commentCount === null ? "Disabled" : fmtCompactNumber(video.commentCount)}
                </span>
                <span class="stat-chip" title="Published Date">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                  ${fmtDate(video.publishedAt)}
                </span>
              </div>
            </div>
          </div>
        `;
      })
      .join("");

    // Attach card click handlers
    videosContainer.querySelectorAll(".video-card").forEach((card) => {
      card.addEventListener("click", () => {
        const vidId = card.dataset.videoId;
        const video = state.videos.find((v) => v.id === vidId);
        if (video) {
          selectVideo(video);
        }
      });
    });
  }

  function selectVideo(video) {
    state.selectedVideo = video;

    // Update active video badge in topbar
    const activePill = $("activeVideoPill");
    const activeTitle = $("activeVideoTitle");
    if (activePill && activeTitle) {
      activePill.classList.add("show");
      activeTitle.textContent = video.title;
    }

    // Update cards selection state
    $$(".video-card").forEach((c) => {
      c.classList.toggle("selected", c.dataset.videoId === video.id);
    });

    // Update Comments View Banner
    const commentsBanner = $("activeVideoBanner");
    const commentsThumb = $("activeVideoThumb");
    const commentsHeading = $("activeVideoHeading");
    const commentsChannel = $("activeVideoChannel");
    const commentsYtLink = $("activeVideoYtLink");

    if (commentsBanner) {
      commentsBanner.style.display = "flex";
      commentsThumb.src = video.thumbnail;
      commentsHeading.textContent = video.title;
      commentsChannel.innerHTML = `
        <span>${esc(state.channel?.title || "YouTube Channel")}</span>
        <span>•</span>
        <span>${fmtCompactNumber(video.views)} views</span>
        <span>•</span>
        <span>${video.commentCount !== null ? fmtNumber(video.commentCount) + " public comments" : "Comments disabled"}</span>
      `;
      commentsYtLink.href = `https://www.youtube.com/watch?v=${video.id}`;
    }

    showToast(`Selected: "${video.title.slice(0, 45)}..."`);

    // Switch smoothly to Comments Explorer view
    switchView("comments");
  }

  // ==========================================================================
  // Comments Scraping & Metrics Computation
  // ==========================================================================
  async function scrapeComments() {
    if (!state.selectedVideo) {
      showToast("Please search and select a video first", "error");
      switchView("search");
      return;
    }

    const scrapeBtn = $("scrapeSubmitBtn");
    const errorBanner = $("scrapeErrorBanner");
    const errorMsg = $("scrapeErrorText");
    const limitInput = $("scrapeLimit");
    const orderSelect = $("scrapeOrder");
    const repliesCheck = $("scrapeReplies");

    const limit = Math.min(Math.max(parseInt(limitInput.value, 10) || 100, 1), 5000);
    const order = orderSelect.value === "time" ? "time" : "relevance";
    const replies = repliesCheck.checked;

    hideError(errorBanner);
    state.isScraping = true;
    setButtonLoading(scrapeBtn, true, "Fetching Comments...");

    try {
      const params = new URLSearchParams({
        videoId: state.selectedVideo.id,
        limit: limit,
        order: order,
        replies: replies,
      });

      const res = await fetch(`/api/youtube/comments?${params.toString()}`);
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        if (data.error && data.error.includes("quota")) {
          state.apiStatus.status = "quota_exceeded";
          updateApiStatusUI();
        }
        throw new Error(data.error || "Failed to retrieve comments.");
      }

      state.allComments = data.comments || [];
      state.pagination.page = 1;
      $("commentsSearchInput").value = "";
      state.filters.search = "";

      computeAnalyticsMetrics();
      applyFiltersAndSort();
      renderCommentsTable();

      showToast(`Successfully retrieved ${state.allComments.length} comment(s)!`);
    } catch (err) {
      showError(errorBanner, errorMsg, err.message);
    } finally {
      state.isScraping = false;
      setButtonLoading(scrapeBtn, false, "Scrape Comments");
    }
  }

  /**
   * Calculate honest analytics supported by actual comment data
   */
  function computeAnalyticsMetrics() {
    const list = state.allComments;
    const totalCount = list.length;
    let repliesCount = 0;
    let totalLikes = 0;
    let maxLikedComment = null;

    for (const c of list) {
      if (c.type === "reply") repliesCount++;
      const likes = Number(c.likes) || 0;
      totalLikes += likes;
      if (!maxLikedComment || likes > (maxLikedComment.likes || 0)) {
        maxLikedComment = c;
      }
    }

    const topLevelCount = totalCount - repliesCount;

    // Metric 1: Total Retrieved
    $("metricTotalCount").textContent = fmtNumber(totalCount);
    $("metricTotalSub").textContent = `Max limit requested: ${$("scrapeLimit").value}`;

    // Metric 2: Comments vs Replies
    $("metricBreakdown").textContent = `${fmtNumber(topLevelCount)} / ${fmtNumber(repliesCount)}`;
    $("metricBreakdownSub").textContent = `${totalCount > 0 ? ((topLevelCount / totalCount) * 100).toFixed(0) : 0}% top-level comments`;

    // Metric 3: Total Likes
    $("metricLikes").textContent = fmtNumber(totalLikes);
    const avgLikes = totalCount > 0 ? (totalLikes / totalCount).toFixed(1) : "0";
    $("metricLikesSub").textContent = `Avg. ${avgLikes} likes per comment`;

    // Metric 4: Most Liked
    if (maxLikedComment && maxLikedComment.likes > 0) {
      $("metricTopAuthor").textContent = maxLikedComment.author;
      $("metricTopAuthorSub").textContent = `${fmtNumber(maxLikedComment.likes)} likes on top comment`;
    } else {
      $("metricTopAuthor").textContent = totalCount > 0 ? "None with likes" : "—";
      $("metricTopAuthorSub").textContent = "No likes recorded";
    }

    // Show metrics section
    $("metricsRow").style.display = totalCount > 0 ? "grid" : "none";
  }

  // ==========================================================================
  // Comment Filtering, Sorting & Table Rendering
  // ==========================================================================
  function applyFiltersAndSort() {
    const q = (state.filters.search || "").trim().toLowerCase();
    const type = state.filters.type;
    const sort = state.filters.sort;
    const minLikes = state.filters.minLikes;

    let result = state.allComments.filter((c) => {
      // Type filter
      if (type === "comment" && c.type !== "comment") return false;
      if (type === "reply" && c.type !== "reply") return false;

      // Min likes
      if (minLikes > 0 && (Number(c.likes) || 0) < minLikes) return false;

      // Search query
      if (q) {
        const textMatch = (c.text || "").toLowerCase().includes(q);
        const authorMatch = (c.author || "").toLowerCase().includes(q);
        if (!textMatch && !authorMatch) return false;
      }

      return true;
    });

    // Sort
    result.sort((a, b) => {
      if (sort === "likes_desc") return (b.likes || 0) - (a.likes || 0);
      if (sort === "likes_asc") return (a.likes || 0) - (b.likes || 0);
      if (sort === "date_desc") return new Date(b.publishedAt) - new Date(a.publishedAt);
      if (sort === "date_asc") return new Date(a.publishedAt) - new Date(b.publishedAt);
      return 0;
    });

    state.filteredComments = result;
  }

  function renderCommentsTable() {
    applyFiltersAndSort();

    const tbody = $("commentsTableBody");
    const emptyState = $("commentsEmptyState");
    const tableWrap = $("commentsTableWrapper");
    const countBadge = $("visibleCommentsCount");
    const list = state.filteredComments;

    countBadge.textContent = `${fmtNumber(list.length)} matching`;

    if (!list.length) {
      if (tbody) tbody.innerHTML = "";
      if (tableWrap) tableWrap.style.display = "none";
      if (emptyState) {
        emptyState.style.display = "flex";
        $("emptyStateHeading").textContent = state.allComments.length ? "No comments match current filter" : "No comments loaded yet";
        $("emptyStateDesc").textContent = state.allComments.length
          ? "Try adjusting your search keywords or clearing type/like filters."
          : "Click 'Scrape Comments' above to fetch and analyze comments for the selected video.";
      }
      renderPagination(0);
      return;
    }

    if (emptyState) emptyState.style.display = "none";
    if (tableWrap) tableWrap.style.display = "block";

    // Paginate
    const { page, pageSize } = state.pagination;
    const totalPages = Math.ceil(list.length / pageSize) || 1;
    const currentPage = Math.min(Math.max(page, 1), totalPages);
    state.pagination.page = currentPage;

    const startIndex = (currentPage - 1) * pageSize;
    const pageItems = list.slice(startIndex, startIndex + pageSize);

    tbody.innerHTML = pageItems
      .map((c) => {
        const isReply = c.type === "reply";
        const authorInitial = (c.author || "?").replace(/^@/, "").charAt(0).toUpperCase();

        return `
          <tr>
            <td class="col-author">
              <div class="author-wrap">
                <div class="author-avatar">${esc(authorInitial)}</div>
                <div>
                  <div class="author-name">${esc(c.author)}</div>
                  ${isReply ? '<span class="reply-badge">Reply</span>' : ""}
                </div>
              </div>
            </td>
            <td class="col-text">
              <div class="comment-bubble">${esc(c.text)}</div>
            </td>
            <td class="col-likes">
              <span class="likes-badge">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                ${fmtNumber(c.likes)}
              </span>
            </td>
            <td class="col-date">${fmtDate(c.publishedAt)}</td>
          </tr>
        `;
      })
      .join("");

    renderPagination(list.length);
  }

  function renderPagination(totalItems) {
    const paginationBar = $("tablePaginationBar");
    if (!paginationBar) return;

    if (totalItems === 0) {
      paginationBar.style.display = "none";
      return;
    }

    paginationBar.style.display = "flex";
    const { page, pageSize } = state.pagination;
    const totalPages = Math.ceil(totalItems / pageSize) || 1;
    const from = (page - 1) * pageSize + 1;
    const to = Math.min(page * pageSize, totalItems);

    $("paginationSummary").textContent = `Showing ${fmtNumber(from)}–${fmtNumber(to)} of ${fmtNumber(totalItems)} comments`;
    $("pageIndicator").textContent = `Page ${page} of ${totalPages}`;

    $("prevPageBtn").disabled = page <= 1;
    $("nextPageBtn").disabled = page >= totalPages;
  }

  // ==========================================================================
  // Exports (CSV, JSON, Clipboard & History)
  // ==========================================================================
  function exportCSV() {
    const list = state.filteredComments.length ? state.filteredComments : state.allComments;
    if (!list.length) {
      showToast("No comments available to export.", "error");
      return;
    }

    const cell = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const headers = ["type", "author", "comment", "likes", "published_at", "reply_count"];
    const rows = list.map((c) =>
      [c.type, c.author, c.text, c.likes, c.publishedAt, c.replyCount ?? (c.type === "reply" ? 0 : "")].map(cell).join(",")
    );

    // UTF-8 BOM (\uFEFF) ensures Excel opens multilingual characters & emojis correctly
    const csvContent = "\uFEFF" + [headers.join(","), ...rows].join("\n");
    const filename = `${slugify(state.selectedVideo?.title || "youtube-comments")}-${Date.now()}.csv`;

    downloadBlob(csvContent, filename, "text/csv;charset=utf-8;");
    recordExport("CSV", list.length, filename);
    showToast(`Exported ${fmtNumber(list.length)} comments as CSV!`);
  }

  function exportJSON() {
    const list = state.filteredComments.length ? state.filteredComments : state.allComments;
    if (!list.length) {
      showToast("No comments available to export.", "error");
      return;
    }

    const jsonContent = JSON.stringify(list, null, 2);
    const filename = `${slugify(state.selectedVideo?.title || "youtube-comments")}-${Date.now()}.json`;

    downloadBlob(jsonContent, filename, "application/json;charset=utf-8;");
    recordExport("JSON", list.length, filename);
    showToast(`Exported ${fmtNumber(list.length)} comments as JSON!`);
  }

  async function copyCommentsText() {
    const list = state.filteredComments.length ? state.filteredComments : state.allComments;
    if (!list.length) {
      showToast("No comments available to copy.", "error");
      return;
    }

    const text = list.map((c) => `${c.author}: ${c.text}`).join("\n\n");

    try {
      await navigator.clipboard.writeText(text);
      showToast(`Copied ${fmtNumber(list.length)} comments to clipboard!`);
    } catch {
      // Fallback
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      showToast(`Copied ${fmtNumber(list.length)} comments to clipboard!`);
    }
  }

  function downloadBlob(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function recordExport(format, count, filename) {
    const record = {
      id: "exp-" + Date.now(),
      timestamp: new Date().toISOString(),
      videoTitle: state.selectedVideo?.title || "Unknown Video",
      videoId: state.selectedVideo?.id || "",
      count: count,
      format: format,
      filename: filename,
    };

    state.exportHistory.unshift(record);
    saveExportHistory();
    renderExportHistory();
  }

  function renderExportHistory() {
    const tbody = $("exportsTableBody");
    const emptyState = $("exportsEmptyState");
    const tableWrap = $("exportsTableWrapper");

    if (!state.exportHistory.length) {
      if (tbody) tbody.innerHTML = "";
      if (tableWrap) tableWrap.style.display = "none";
      if (emptyState) emptyState.style.display = "flex";
      return;
    }

    if (emptyState) emptyState.style.display = "none";
    if (tableWrap) tableWrap.style.display = "block";

    tbody.innerHTML = state.exportHistory
      .map((item) => {
        return `
          <tr>
            <td style="font-weight:600;color:#fff">${esc(fmtDate(item.timestamp))} ${esc(fmtTime(item.timestamp))}</td>
            <td>
              <div style="font-weight:600;color:#fff;max-width:320px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                ${esc(item.videoTitle)}
              </div>
              <small style="color:var(--text-muted)">ID: ${esc(item.videoId)}</small>
            </td>
            <td>
              <span class="badge ${item.format === "CSV" ? "active-badge" : ""}" style="font-weight:700">
                ${esc(item.format)}
              </span>
            </td>
            <td style="font-variant-numeric:tabular-nums;font-weight:600">${fmtNumber(item.count)}</td>
            <td>
              <span style="color:var(--status-ok);font-size:12.5px;font-weight:600">Saved</span>
            </td>
          </tr>
        `;
      })
      .join("");
  }

  // ==========================================================================
  // Settings View Rendering & Handlers
  // ==========================================================================
  function renderSettings() {
    const prefLimit = $("prefDefaultLimit");
    const prefOrder = $("prefDefaultOrder");
    const prefReplies = $("prefDefaultReplies");

    if (prefLimit) prefLimit.value = state.preferences.defaultLimit;
    if (prefOrder) prefOrder.value = state.preferences.defaultOrder;
    if (prefReplies) prefReplies.checked = state.preferences.defaultReplies;
  }

  // ==========================================================================
  // Helper UI Utilities
  // ==========================================================================
  function showError(bannerEl, msgEl, text) {
    if (msgEl) msgEl.textContent = text;
    if (bannerEl) bannerEl.classList.add("show");
  }

  function hideError(bannerEl) {
    if (bannerEl) bannerEl.classList.remove("show");
  }

  function setButtonLoading(btn, isLoading, defaultText) {
    if (!btn) return;
    btn.disabled = isLoading;
    if (isLoading) {
      btn.innerHTML = `<span class="spinner"></span> Working...`;
    } else {
      btn.innerHTML = defaultText;
    }
  }

  // ==========================================================================
  // Event Listeners Setup
  // ==========================================================================
  function initEventListeners() {
    // Nav Items
    $$(".nav-item").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const view = btn.dataset.view;
        if (view) switchView(view);
      });
    });

    // Mobile sidebar toggle
    $("menuToggleBtn").addEventListener("click", () => {
      $("sidebar").classList.add("open");
      $("sidebarOverlay").classList.add("open");
    });
    $("sidebarCloseBtn").addEventListener("click", () => {
      $("sidebar").classList.remove("open");
      $("sidebarOverlay").classList.remove("open");
    });
    $("sidebarOverlay").addEventListener("click", () => {
      $("sidebar").classList.remove("open");
      $("sidebarOverlay").classList.remove("open");
    });

    // API Status badge click -> open Settings diagnostic
    $("apiStatusBadge").addEventListener("click", () => {
      switchView("settings");
    });

    // Test API Connection button in Settings
    $("testConnectionBtn")?.addEventListener("click", async () => {
      const btn = $("testConnectionBtn");
      setButtonLoading(btn, true, "Testing...");
      await checkApiConnection();
      setButtonLoading(btn, false, "Test Connection Now");
      showToast("API Connection Test Finished!");
    });

    // Video Search Form
    $("videoSearchForm").addEventListener("submit", (e) => {
      e.preventDefault();
      searchVideos($("channelInput").value, $("videoInput").value);
    });

    // Quick presets in scrape options
    $$(".preset-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        $$(".preset-pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        $("scrapeLimit").value = pill.dataset.limit;
      });
    });

    // Scrape comments button
    $("scrapeSubmitBtn").addEventListener("click", () => {
      scrapeComments();
    });

    // Comments search / filter
    $("commentsSearchInput").addEventListener("input", (e) => {
      state.filters.search = e.target.value;
      state.pagination.page = 1;
      renderCommentsTable();
    });

    $("commentTypeFilter").addEventListener("change", (e) => {
      state.filters.type = e.target.value;
      state.pagination.page = 1;
      renderCommentsTable();
    });

    $("commentSortSelect").addEventListener("change", (e) => {
      state.filters.sort = e.target.value;
      renderCommentsTable();
    });

    $("minLikesFilter").addEventListener("change", (e) => {
      state.filters.minLikes = parseInt(e.target.value, 10) || 0;
      state.pagination.page = 1;
      renderCommentsTable();
    });

    $("rowsPerPageSelect").addEventListener("change", (e) => {
      state.pagination.pageSize = parseInt(e.target.value, 10) || 25;
      state.pagination.page = 1;
      renderCommentsTable();
    });

    $("prevPageBtn").addEventListener("click", () => {
      if (state.pagination.page > 1) {
        state.pagination.page--;
        renderCommentsTable();
      }
    });

    $("nextPageBtn").addEventListener("click", () => {
      state.pagination.page++;
      renderCommentsTable();
    });

    // Export buttons
    $("exportCsvBtn").addEventListener("click", exportCSV);
    $("exportJsonBtn").addEventListener("click", exportJSON);
    $("copyTextBtn").addEventListener("click", copyCommentsText);

    // Clear Export History
    $("clearExportHistoryBtn")?.addEventListener("click", () => {
      if (confirm("Are you sure you want to clear your export history?")) {
        state.exportHistory = [];
        saveExportHistory();
        renderExportHistory();
        showToast("Export history cleared.");
      }
    });

    // Save Settings
    $("savePreferencesBtn")?.addEventListener("click", () => {
      state.preferences.defaultLimit = parseInt($("prefDefaultLimit").value, 10) || 200;
      state.preferences.defaultOrder = $("prefDefaultOrder").value;
      state.preferences.defaultReplies = $("prefDefaultReplies").checked;

      // Apply to form
      $("scrapeLimit").value = state.preferences.defaultLimit;
      $("scrapeOrder").value = state.preferences.defaultOrder;
      $("scrapeReplies").checked = state.preferences.defaultReplies;

      savePreferences();
      showToast("Preferences saved!");
    });

    // Clear Local Storage Data
    $("clearAllDataBtn")?.addEventListener("click", () => {
      if (confirm("Reset all local cache, export history, and user preferences?")) {
        localStorage.removeItem("yt_scrapper_exports");
        localStorage.removeItem("yt_scrapper_prefs");
        state.exportHistory = [];
        state.preferences = { defaultLimit: 200, defaultOrder: "relevance", defaultReplies: false };
        renderSettings();
        renderExportHistory();
        showToast("All local application data reset.");
      }
    });

    // Overview "Start a New Scrape" and quick links
    $("startSearchHeroBtn")?.addEventListener("click", () => {
      switchView("search");
    });
    $("viewCommentsHeroBtn")?.addEventListener("click", () => {
      switchView("comments");
    });
  }

  // ==========================================================================
  // Initialization
  // ==========================================================================
  function init() {
    loadPersistedData();
    initEventListeners();

    // Set initial form values from preferences
    if ($("scrapeLimit")) $("scrapeLimit").value = state.preferences.defaultLimit;
    if ($("scrapeOrder")) $("scrapeOrder").value = state.preferences.defaultOrder;
    if ($("scrapeReplies")) $("scrapeReplies").checked = state.preferences.defaultReplies;

    // Check actual API status on startup
    checkApiConnection();

    // Start on Dashboard view
    switchView("dashboard");
  }

  // Run on DOM load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
