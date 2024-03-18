import * as React from 'react';
import { Component } from 'react';
import PropTypes from 'prop-types';

import "../styles/start.css"
import KeywordColumn from './components/KeywordColumn';

/**
 * Keywords is a class that returns the tab screen for relevant and blacklisted keywords. 
 */
class Keywords extends Component {

    // Getter for relevant keywords
    get relevantKeywords() {
        return this.props.keywords.relevantKeywords;
    }

    // Getter for blacklisted keywords
    get blacklistedKeywords() {
        return this.props.keywords.blacklistedKeywords;
    }

    /**
     * Updates the current keyword lists to the TabScreen
     */
    updateKeywords(relevantKeywords, blacklistedKeywords) {
        this.props.saveConfiguration({
            relevantKeywords,
            blacklistedKeywords
        });
    }

    /**
     * Adds the newly submitted relevant keyword to the list 
     */
    addRelevantKeyword(keyword) {
        this.updateKeywords(
            this.relevantKeywords.concat([keyword]),
            this.blacklistedKeywords
        );
    }

    /**
     * Adds the newly submitted blacklisted keyword to the list 
     */
    addBlacklistedKeyword(keyword) {
        this.updateKeywords(
            this.relevantKeywords,
            this.blacklistedKeywords.concat([keyword])
        );
    }

    /**
     * Clears the list of relevant keywords
     */
    clearRelevantKeywords() {
        this.updateKeywords(
            [],
            this.blacklistedKeywords
        );
    }

    /**
     * Clears the list of blacklisted keywords
     */
    clearBlacklistedKeywords() {
        this.updateKeywords(
            this.relevantKeywords,
            []
        );
    }

    render() {
        return (
            <div className="KeywordsTab">
                <div>
                    {/* Column for the relevant keywords */}
                    <KeywordColumn
                        name="Relevant keywords"
                        keywordsList={this.relevantKeywords}
                        addKeyword={this.addRelevantKeyword.bind(this)}
                        clear={this.clearRelevantKeywords.bind(this)}
                    />

                    {/* Column for the blacklisted keywords */}
                    <KeywordColumn
                        name="Blacklisted keywords"
                        keywordsList={this.blacklistedKeywords}
                        addKeyword={this.addBlacklistedKeyword.bind(this)}
                        clear={this.clearBlacklistedKeywords.bind(this)}
                    />
                </div>
            </div>
        )
    }
}

// Define the props of this class
Keywords.propTypes = {
    keywords: PropTypes.shape({
        relevantKeywords: PropTypes.array.isRequired,
        blacklistedKeywords: PropTypes.array.isRequired
    }).isRequired,
    saveConfiguration: PropTypes.func.isRequired
};

export default Keywords