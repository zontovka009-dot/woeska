import { useEffect, useRef, useState } from 'react';

let ytPromise: Promise<any> | null = null;

function loadYT() {
  if ((window as any).YT?.Player) return Promise.resolve((window as any).YT);
  if (ytPromise) return ytPromise;

  ytPromise = new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(script);
    (window as any).onYouTubeIframeAPIReady = () => resolve((window as any).YT);
  });

  return ytPromise;
}

type SkipDirection = 'left' | 'right';

export function VideoPlayer({
  room,
  playing,
  position,
  onPlay,
  onPause,
  onSeek,
}: any) {
  const host = useRef<HTMLDivElement>(null);
  const player = useRef<any>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const hideTimer = useRef<number | null>(null);

  const [progress, setProgress] = useState(position || 0);
  const [duration, setDuration] = useState(0);
  const [quality, setQuality] = useState('auto');
  const [menu, setMenu] = useState(false);
  const [controls, setControls] = useState(true);
  const [skipFlash, setSkipFlash] = useState<SkipDirection | null>(null);
  const [muted, setMuted] = useState(false);

  const provider = room?.provider;

  useEffect(() => {
    setProgress(position || 0);
  }, [position]);

  useEffect(() => {
    let alive = true;

    if (provider === 'youtube') {
      loadYT().then((YT: any) => {
        if (!alive || !host.current) return;

        player.current = new YT.Player(host.current, {
          videoId: room.video_id,
          playerVars: {
            playsinline: 1,
            controls: 0,
            rel: 0,
            modestbranding: 1,
            disablekb: 1,
          },
          events: {
            onReady: (event: any) => {
              setDuration(event.target.getDuration());
              if (playing) event.target.playVideo();
            },
            onStateChange: (event: any) => {
              if (event.data === 1) onPlay?.();
              if (event.data === 2) onPause?.();
            },
          },
        });
      });
    }

    return () => {
      alive = false;
      player.current?.destroy?.();
      player.current = null;
    };
  }, [provider, room?.video_id]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (player.current?.getCurrentTime) {
        setProgress(player.current.getCurrentTime());
      }
    }, 500);

    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!player.current) return;

    if (playing) {
      player.current.playVideo?.();
    } else {
      player.current.pauseVideo?.();
    }
  }, [playing]);

  useEffect(() => {
    return () => {
      if (hideTimer.current !== null) window.clearTimeout(hideTimer.current);
    };
  }, []);

  function showControls() {
    setControls(true);

    if (hideTimer.current !== null) window.clearTimeout(hideTimer.current);
    hideTimer.current = window.setTimeout(() => setControls(false), 3000);
  }

  function flashSkip(direction: SkipDirection) {
    setSkipFlash(direction);
    window.setTimeout(() => setSkipFlash(null), 520);
    showControls();
  }

  function seekBy(delta: number) {
    const next = Math.max(0, Math.min(duration || Infinity, progress + delta));

    if (player.current?.seekTo) {
      player.current.seekTo(next, true);
    } else {
      onSeek?.(next);
    }

    setProgress(next);
    onSeek?.(next);
    flashSkip(delta < 0 ? 'left' : 'right');
  }

  function seekTo(value: string) {
    const next = Number(value);

    if (player.current?.seekTo) {
      player.current.seekTo(next, true);
    }

    setProgress(next);
    onSeek?.(next);
  }

  function setQ(value: string) {
    setQuality(value);
    setMenu(false);

    const map: Record<string, string> = {
      auto: 'default',
      '1080p': 'hd1080',
      '720p': 'hd720',
      '480p': 'large',
    };

    player.current?.setPlaybackQuality?.(map[value] || 'default');
    showControls();
  }

  function toggleMute() {
    if (!player.current) return;

    if (muted) {
      player.current.unMute?.();
    } else {
      player.current.mute?.();
    }

    setMuted((value) => !value);
    showControls();
  }

  async function toggleFullscreen() {
    try {
      if (!document.fullscreenElement) {
        await wrap.current?.requestFullscreen?.();
      } else {
        await document.exitFullscreen?.();
      }
    } catch {
      // Fullscreen can be unavailable in Telegram's webview.
    }
  }

  const src =
    provider === 'vk'
      ? `https://vk.com/video_ext.php?oid=${room.video_id?.split('_')[0]}&id=${room.video_id?.split('_')[1]}&js_api=1`
      : provider === 'drive'
        ? `https://drive.google.com/file/d/${room.video_id}/preview`
        : '';

  if (!provider) {
    return (
      <div className="empty-player wathis-player-empty">
        <div className="play-orb wathis-player-orb">▶</div>
        <div>
          <strong>Видео пока не выбрано</strong>
          <span>Добавь ссылку выше, чтобы начать просмотр</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`player-shell wathis-player ${controls ? 'show-controls' : ''}`}
      ref={wrap}
      onMouseMove={showControls}
      onTouchStart={showControls}
    >
      <div className="player-video-layer">
        {provider === 'youtube' ? (
          <div ref={host} className="video-frame" />
        ) : (
          <iframe
            className="video-frame"
            src={src}
            allow="autoplay; fullscreen; picture-in-picture"
            allowFullScreen
            title="Wathis player"
          />
        )}
      </div>

      <div className="player-vignette" aria-hidden="true" />
      <div className="player-source-badge">
        <span className="source-dot" />
        {provider === 'youtube' ? 'YouTube' : provider === 'vk' ? 'VK Video' : 'Google Drive'}
      </div>

      <div className="tap-zone left" onDoubleClick={() => seekBy(-10)} onClick={showControls} />
      <div
        className="tap-zone center"
        onClick={() => {
          playing ? onPause?.() : onPlay?.();
          showControls();
        }}
      />
      <div className="tap-zone right" onDoubleClick={() => seekBy(10)} onClick={showControls} />

      <div className="player-overlay" aria-hidden="true">
        <div className={`skip-hint left-hint ${skipFlash === 'left' ? 'active' : ''}`}>
          <span className="skip-arrow">↶</span>
          <b>10</b>
        </div>
        <div className={`skip-hint right-hint ${skipFlash === 'right' ? 'active' : ''}`}>
          <b>10</b>
          <span className="skip-arrow">↷</span>
        </div>
      </div>

      <button
        className={`player-center-button ${playing ? 'is-playing' : ''}`}
        onClick={() => (playing ? onPause?.() : onPlay?.())}
        aria-label={playing ? 'Пауза' : 'Воспроизвести'}
      >
        <span>{playing ? 'Ⅱ' : '▶'}</span>
      </button>

      <div className="player-controls">
        <div className="seek-wrap">
          <input
            className="seekbar"
            type="range"
            min="0"
            max={duration || 100}
            step="0.1"
            value={Math.min(progress, duration || 100)}
            onChange={(event) => seekTo(event.target.value)}
            aria-label="Прогресс видео"
          />
        </div>

        <div className="controls-row">
          <button className="player-control skip-button" onClick={() => seekBy(-10)} aria-label="Назад на 10 секунд">
            <span>↶</span>
            <small>10</small>
          </button>

          <button
            className="player-control compact-play"
            onClick={() => (playing ? onPause?.() : onPlay?.())}
            aria-label={playing ? 'Пауза' : 'Воспроизвести'}
          >
            {playing ? 'Ⅱ' : '▶'}
          </button>

          <button className="player-control skip-button" onClick={() => seekBy(10)} aria-label="Вперёд на 10 секунд">
            <small>10</small>
            <span>↷</span>
          </button>

          <span className="time">{fmt(progress)} / {fmt(duration)}</span>

          <div className="control-spacer" />

          {provider === 'youtube' && (
            <div className="quality-wrap">
              <button className="player-control glass-button" onClick={() => setMenu((value) => !value)}>
                <span className="control-icon">HD</span>
                <span>{quality}</span>
                <span className="chevron">⌄</span>
              </button>
              {menu && (
                <div className="quality-menu">
                  {['auto', '1080p', '720p', '480p'].map((value) => (
                    <button key={value} onClick={() => setQ(value)} className={value === quality ? 'selected' : ''}>
                      <span>{value}</span>
                      {value === quality && <span>✓</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <button className="player-control glass-button" onClick={toggleMute} aria-label={muted ? 'Включить звук' : 'Выключить звук'}>
            <span className="volume-icon">{muted ? '×' : ')))'}</span>
          </button>

          <button className="player-control glass-button fullscreen-button" onClick={toggleFullscreen} aria-label="Полный экран">
            ⛶
          </button>
        </div>
      </div>
    </div>
  );
}

function fmt(value: number) {
  if (!value || !isFinite(value)) return '00:00';

  return `${Math.floor(value / 60)
    .toString()
    .padStart(2, '0')}:${Math.floor(value % 60)
    .toString()
    .padStart(2, '0')}`;
}
