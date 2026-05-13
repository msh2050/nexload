// Compose all Nexload concepts into a single design canvas
const { useState, useEffect } = React;

function Frame({ children, dark = true, radius = 18 }) {
  return (
    <div style={{
      width: '100%', height: '100%', overflow: 'hidden',
      borderRadius: radius,
      boxShadow: dark
        ? '0 30px 80px rgba(0,0,0,0.55), 0 4px 14px rgba(0,0,0,0.3)'
        : '0 30px 80px rgba(40,40,60,0.18), 0 4px 14px rgba(40,40,60,0.10)',
    }}>
      {children}
    </div>
  );
}

function NexloadCanvas() {
  return (
    <DesignCanvas title="Nexload — concept exploration" subtitle="A modern download manager · light + dark, with charm">

      <DCSection id="dashboards" title="Main Dashboard" subtitle="Active downloads · dark glass hero + light alt">
        <DCArtboard id="dash-dark" label="A · Dark glass (hero)" width={1280} height={800}>
          <Frame><DashboardDark/></Frame>
        </DCArtboard>
        <DCArtboard id="dash-light" label="B · Light · airy" width={1280} height={800}>
          <Frame dark={false}><DashboardLight/></Frame>
        </DCArtboard>
      </DCSection>

      <DCSection id="dropzone" title="Floating drop zone" subtitle="Tiny desktop widget · three states">
        <DCArtboard id="drop-idle" label="Idle" width={300} height={300}>
          <DropIdle/>
        </DCArtboard>
        <DCArtboard id="drop-hover" label="Drag over · portal open" width={300} height={300}>
          <DropHover/>
        </DCArtboard>
        <DCArtboard id="drop-recv" label="Receiving" width={300} height={300}>
          <DropReceiving/>
        </DCArtboard>
      </DCSection>

      <DCSection id="sniffer" title="Video sniffer" subtitle="In-browser detection toast">
        <DCArtboard id="sniffer-toast" label="On a video page" width={420} height={520}>
          <Frame><SnifferToast/></Frame>
        </DCArtboard>
        <DCArtboard id="complete" label="Download complete moment" width={620} height={520}>
          <Frame><CompleteMoment/></Frame>
        </DCArtboard>
      </DCSection>

      <DCSection id="empty" title="Empty state" subtitle="Tide, the sleeping mascot — serene landscape">
        <DCArtboard id="empty-tide" label="No active downloads" width={1280} height={760}>
          <Frame><EmptyState/></Frame>
        </DCArtboard>
      </DCSection>

      <DCSection id="library" title="Completed library" subtitle="Rich, gallery-style review of finished downloads">
        <DCArtboard id="lib-grid" label="Grid view" width={1280} height={760}>
          <Frame><CompletedLibrary/></Frame>
        </DCArtboard>
      </DCSection>

      <DCSection id="settings" title="Settings" subtitle="Powerhouse hidden behind a calm surface">
        <DCArtboard id="set-conn" label="Connection" width={1280} height={760}>
          <Frame><SettingsPanel/></Frame>
        </DCArtboard>
      </DCSection>

      <DCSection id="studies" title="Progress studies" subtitle="Six different visualizations to mix-and-match">
        <DCArtboard id="prog-studies" label="Six bars" width={1000} height={520}>
          <Frame><ProgressStudies/></Frame>
        </DCArtboard>
      </DCSection>

    </DesignCanvas>
  );
}

ReactDOM.createRoot(document.getElementById('app')).render(<NexloadCanvas/>);
