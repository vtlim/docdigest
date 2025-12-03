import React from 'react';
import DocCardList from '@theme-original/DocCardList';
import {useCurrentSidebarCategory} from '@docusaurus/plugin-content-docs/client';

let summaries = {};
try {
  summaries = require('@site/static/js/summaries');
} catch (e) {
  console.warn('summaries.js not found');
}

export default function DocCardListWrapper(props) {
  const category = useCurrentSidebarCategory();
  const items = props.items || category?.items || [];

  const itemsWithDescriptions = items.map(item => {
    let docId;
    
    if (item.type === 'link') {
      docId = item.docId;
    } else if (item.type === 'category' && item.href) {
      // Extract docId from href like '/lumi/send-events/s2s' -> 'send-events/s2s'
      docId = item.href.replace('/lumi/', '');
    }
    
    if (docId) {
      const key = docId.replace(/\//g, '_').replace(/-/g, '_');
      const customSummary = summaries[key];
      
      if (customSummary) {
        return { ...item, description: customSummary };
      }
    }
    
    return item;
  });

  return <DocCardList {...props} items={itemsWithDescriptions} />;
}
