// Mechanical tracks use absolute monotonic anchors, never frame-count increments.
// Background policy: freeze both tracks while hidden, then resume at the same pose.
export function createPresentationClock({now=()=>performance.now()}={}) {
  let speed=1,hidden=false,last=now();
  const tracks={mechanism:{offset:0,anchor:last,running:false},hands:{offset:0,anchor:last,running:false}};
  const time=value=>{if(!Number.isFinite(value))throw new TypeError('Clock timestamp must be finite.');return Math.max(last,value);};
  const valueAt=(track,t)=>track.offset+(!hidden&&track.running?(t-track.anchor)*speed/1000:0);
  const settle=t=>{for(const track of Object.values(tracks)){track.offset=valueAt(track,t);track.anchor=t;}};
  const snapshot=t=>({mechanism:valueAt(tracks.mechanism,t),hands:valueAt(tracks.hands,t),speed,hidden,
    running:{mechanism:tracks.mechanism.running,hands:tracks.hands.running},backgroundPolicy:'pause while hidden'});
  return {
    tick(timestamp=now()){const t=time(timestamp),delta=hidden?0:(t-last)/1000;last=t;return {...snapshot(t),delta};},
    snapshot(timestamp=now()){return snapshot(time(timestamp));},
    setRunning(track,running,timestamp=now()) {
      if(!(track in tracks))throw new TypeError('Unknown mechanical clock track.');
      const t=time(timestamp),entry=tracks[track];entry.offset=valueAt(entry,t);entry.anchor=t;entry.running=!!running;last=t;
      return snapshot(t);
    },
    setSpeed(value,timestamp=now()) {
      if(!Number.isFinite(value)||value<=0)throw new TypeError('Clock speed must be positive and finite.');
      const t=time(timestamp);settle(t);speed=value;last=t;return snapshot(t);
    },
    setHidden(value,timestamp=now()) {
      const t=time(timestamp);settle(t);hidden=!!value;last=t;return snapshot(t);
    },
    seek(seconds,{track='both',timestamp=now()}={}) {
      if(!Number.isFinite(seconds)||seconds<0)throw new TypeError('Requested time must be non-negative and finite.');
      if(track!=='both'&&!(track in tracks))throw new TypeError('Unknown mechanical clock track.');
      const t=time(timestamp);settle(t);
      for(const name of track==='both'?Object.keys(tracks):[track]){tracks[name].offset=seconds;tracks[name].anchor=t;}
      last=t;return snapshot(t);
    },
    reset(timestamp=now()) {
      const t=time(timestamp);for(const track of Object.values(tracks))Object.assign(track,{offset:0,anchor:t,running:false});
      last=t;return snapshot(t);
    },
  };
}
