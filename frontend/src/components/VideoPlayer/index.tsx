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

  const [progress, setProgress] = useState(position || 0);
  const [duration, setDuration] = useState(0);
  const [quality, setQuality] = useState('auto');
  const [menu, setMenu] = useState(false);
  const [controls, setControls] = useState(true);
  const [skipFlash, setSkipFlash] = useState<'left' | 'right' | null>(null);

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

  function flashSkip(direction: 'left' | 'right') {
    setSkipFlash(direction);
    window.setTimeout(() => setSkipFlash(null), 420);
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
      <div className="empty-player">
        <div className="play-orb">▶</div>
        <span>Добавь видео по ссылке</span>
      </div>
    );
  }

  return (
    <div
      className={`player-shell ${controls ? 'show-controls' : ''}`}
      ref={wrap}
      onMouseMove={() => setControls(true)}
    >
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

      <div
        className="tap-zone left"
        onDoubleClick={() => seekBy(-10)}
        onClick={() => setControls((value) => !value)}
      />
      <div
        className="tap-zone center"
        onClick={() => (playing ? onPause?.() : onPlay?.())}
      />
      <div
        className="tap-zone right"
        onDoubleClick={() => seekBy(10)}
        onClick={() => setControls((value) => !value)}
      />

      <div className="player-overlay" aria-hidden="true">
        <div className={`skip-hint left-hint ${skipFlash === 'left' ? 'active' : ''}`}>
          <span>↶</span>
          <b>10</b>
        </div>
        <div className={`skip-hint right-hint ${skipFlash === 'right' ? 'active' : ''}`}>
          <b>10</b>
          <span>↷</span>
        </div>
      </div>

      <div className="player-controls">
        <input
          className="seekbar"
          type="range"
          min="0"
          max={duration || 100}
          step="0.1"
          value={Math.min(progress, duration || 100)}
          onChange={(event) => seekTo(event.target.value)}
        />

        <div className="controls-row">
          <button className="player-control skip-button" onClick={() => seekBy(-10)} aria-label="Назад на 10 секунд">
            <span>↶</span>
            <small>10</small>
          </button>

          <button
            className="player-control main-play"
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

          <div className="quality-wrap">
            {provider === 'youtube' ? (
              <>
                <button className="player-control quality-button" onClick={() => setMenu((value) => !value)}>
                  HD · {quality}⌄
                </button>
                {menu && (
                  <div className="quality-menu">
                    {['auto', '1080p', '720p', '480p'].map((value) => (
                      <button key={value} onClick={() => setQ(value)}>
                        {value}
                        {value === quality ? ' ✓' : ''}
                      </button>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <button className="player-control quality-disabled" title="Качество управляется источником">
                HD · авто
              </button>
            )}
          </div>

          <button className="player-control fullscreen-button" onClick={toggleFullscreen} aria-label="Полный экран">
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
