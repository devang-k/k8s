
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: PrivacyPolicy.js  
 * Description: This file is responsible to show Privacy Policy. 
 *  
 * Author: [Author's Name]  
 * Created On: [Creation Date]  
 *  
 * Revision History:  
 * - [Date] [Modifier's Name]: [JIRA Id]:[Summary of changes made]  
 *  
 * This source code and associated materials are the property of SiClarity, Inc.  
 * Unauthorized copying, modification, distribution, or use of this software,  
 * in whole or in part, is strictly prohibited without prior written permission  
 * from SiClarity, Inc.  
 *  
 * Disclaimer:  
 * This software is provided "as is," without any express or implied warranties,  
 * including but not limited to warranties of merchantability, fitness for a  
 * particular purpose, or non-infringement. In no event shall SiClarity, Inc.  
 * be held liable for any damages arising from the use of this software.  
 *  
 * SiClarity and its logo are trademarks of SiClarity, Inc.  
 *  
 * For inquiries, contact: support@siclarity.com  
 ***************************************************************************/

import React from "react";

function PrivacyPolicy() {
  return (
    <>
      <div className="container-fluid app-secondary-color" style={{minHeight:"100%", margin:"0px"}} >
        <div className="row" style={{ height: "100%" }}>
          <h3 className="d-flex justify-content-center ">Privacy Policy</h3>
          <hr style={{
            width: "9%",
            margin: "0px auto",
            height: "1px",
            backgroundColor: "black",
            border: "none",
          }} />
          <div className="col-12 mt-3">
            <h5>Last updated December 13 2024 </h5>
            <p>
              This Privacy Notice for SiClarity, Inc. ("we," "us," or "our"), describes how and why we might access, collect, store, use, and/or share ("process") your personal information when you use our services ("Services"), including when you:
            </p>
            <ul>
              <li>Visit our website at <a href="http://www.siclarity.com">http://www.siclarity.com</a>, or any website of ours that links to this Privacy Notice</li>
              <li>Engage with us in other related ways, including any sales, marketing, or events</li>
            </ul>
            <p>
              Questions or concerns? Reading this Privacy Notice will help you understand your privacy rights and choices. We are responsible for making decisions about how your personal information is processed. If you do not agree with our policies and practices, please do not use our Services. If you still have any questions or concerns, please contact us at contact@siclarity.com.
            </p>
          </div>

          <div className="col-12">
            <h5 >SUMMARY OF KEY POINTS</h5>
            <p>This summary provides key points from our Privacy Notice, but you can find out more details about any of these topics by clicking the link following each key point or by using our <a href="#table-contents"> table of contents</a> below to find the section you are looking for.</p>
            <p>What personal information do we process? When you visit, use, or navigate our Services, we may process personal information depending on how you interact with us and the Services, the choices you make, and the products and features you use. Learn more about <a href="#section1">personal information you disclose to us</a>.</p>
            <p>Do we process any sensitive personal information? Some of the information may be considered "special" or "sensitive" in certain jurisdictions, for example your racial or ethnic origins, sexual orientation, and religious beliefs. We do not process sensitive personal information.</p>
            <p>Do we collect any information from third parties? We do not collect any information from third parties.</p>
            <p>How do we process your information? We process your information to provide, improve, and administer our Services, communicate with you, for security and fraud prevention, and to comply with law. We may also process your information for other purposes with your consent. We process your information only when we have a valid legal reason to do so. Learn more about <a href="#section2">how we process your information</a>.</p>
            <p>In what situations and with which parties do we share personal information? We may share information in specific situations and with specific third parties. Learn more about <a href="#section4">when and with whom we share your personal information</a>.</p>
            <p>How do we keep your information safe? We have adequate organizational and technical processes and procedures in place to protect your personal information. However, no electronic transmission over the internet or information storage technology can be guaranteed to be 100% secure, so we cannot promise or guarantee that hackers,
              cybercriminals, or other unauthorized third parties will not be able to defeat our security and improperly collect, access, steal, or modify your information. Learn more about <a href="#section7">how we keep your information safe</a>.</p>
            <p>What are your rights? Depending on where you are located geographically, the applicable privacy law may mean you have certain rights regarding your personal information. Learn more about your <a href="#section9">privacy rights</a>.</p>
            <p>How do you exercise your rights? The easiest way to exercise your rights is by submitting a <a href="https://app.termly.io/notify/e004b96c-767a-4b62-8a3e-8a2fd0405">data subject access request</a>, or by contacting us. We will consider and act upon any request in accordance with applicable data protection laws.</p>
            <p>Want to learn more about what we do with any information we collect?<a href="#table-contents">Review the Privacy Notice in full</a>.</p>
          </div>
          <div className="col-12">
            <h5 id= "table-contents">TABLE OF CONTENTS</h5>
            <ol>
            <li><a href="#section1">WHAT INFORMATION DO WE COLLECT?</a></li>
            <li><a href="#section2">HOW DO WE PROCESS YOUR INFORMATION?</a></li>
              <li><a href="#section3">WHAT LEGAL BASES DO WE RELY ON TO PROCESS YOUR PERSONAL INFORMATION?</a></li>
              <li><a href="#section4">WHEN AND WITH WHOM DO WE SHARE YOUR PERSONAL INFORMATION?</a></li>
              <li><a href="#section5">DO WE USE COOKIES AND OTHER TRACKING TECHNOLOGIES?
              </a></li>
              <li><a href="#section6"> HOW LONG DO WE KEEP YOUR INFORMATION?</a></li>
              <li><a href="#section7">HOW DO WE KEEP YOUR INFORMATION SAFE?</a></li>
              <li><a href="#section8">DO WE COLLECT INFORMATION FROM MINORS?</a></li>
              <li><a href="#section9"> WHAT ARE YOUR PRIVACY RIGHTS?</a></li>
              <li><a href="#section10">CONTROLS FOR DO-NOT-TRACK FEATURES</a></li>
              <li><a href="#section11">DO UNITED STATES RESIDENTS HAVE SPECIFIC PRIVACY RIGHTS?</a></li>
              <li><a href="#section12">DO WE MAKE UPDATES TO THIS NOTICE?</a></li>
              <li><a href="#section13">HOW CAN YOU CONTACT US ABOUT THIS NOTICE?</a></li>
              <li><a href="#section14">HOW CAN YOU REVIEW, UPDATE, OR DELETE THE DATA WE COLLECT FROM YOU?</a></li>
            </ol>
          </div>

          <div className="col-12">
            <h5 id="section1" >1. WHAT INFORMATION DO WE COLLECT?</h5>
            <h5> Personal information you disclose to us
            </h5>
            <p>In Short: We collect personal information that you provide to us.
            </p>
            <p>We collect personal information that you voluntarily provide to us when you register on the Services, express an interest in obtaining information about us or our products and Services, when you participate in activities on the Services, or otherwise when you contact us.</p>
            <p>Personal Information Provided by You. The personal information that we collect depends on the context of your interactions with us and the Services, the choices you make, and the products and features you use. The personal information we collect may include the following:</p>
            <ul>
              <li>names</li>
              <li>phone numbers</li>
              <li>email addresses</li>
              <li>job titles</li>
              <li>usernames</li>
              <li>passwords</li>
              <li>contact preferences</li>
              <li>contact or authentication data</li>
            </ul>
            <p>Sensitive Information. We do not process sensitive information.</p>
            <p>All personal information that you provide to us must be true, complete, and accurate, and you must notify us of any changes to such personal information.</p>
          </div>
          <div className="col-12">
            <h5 >Information automatically collected
            </h5>
            <p>In Short: Some information such as your Internet Protocol (IP) address and/or browser and device characteristics-is collected automatically when you visit our Services.</p>
            <p>We automatically collect certain information when you visit, use, or navigate the Services. This information does not reveal your specific identity (like your name or contact information) but may include device and usage information, such as your IP address, browser and device characteristics, operating system, language preferences, referring URLs, device name, country, location, information about how and when you use our Services, and other technical information. This information is primarily needed to maintain the security and operation of our Services, and for our internal analytics and reporting purposes.</p>
            <p>Like many businesses, we also collect information through cookies and similar technologies. You can find out more about this in our Cookie Notice: <a href="http://www.siclarity.com/cookies">http://www.siclarity.com/cookies.</a></p>
            <p>The information we collect includes:</p>
            <ul>
              <li> Log and Usage Data. Log and usage data is service-related, diagnostic, usage, and performance information our servers automatically collect when you access or use our Services and which we record in log files. Depending on how you interact with us, this log data may include your IP address, device information, browser type, and settings and information about your activity in the Services (such as the date/time stamps associated with your usage, pages and files viewed, searches, and other actions you take such as which features you use), device event information (such as system activity, error reports (sometimes called "crash dumps"), and hardware settings).</li>
              <li>Location Data. We collect location data such as information about your device's location, which can be either precise or imprecise. How much information we collect depends on the type and settings of the device you use to access the Services. For example, we may use GPS and other technologies to collect geolocation data that tells us your current location (based on your IP address). You can opt out of allowing us to collect this information either by refusing access to the information or by disabling your Location setting on your device. However, if you choose to opt out, you may not be able to use certain aspects of the Services.</li>
            </ul>
          </div>

          <div className="col-12">
            <h5 id="section2" >2. HOW DO WE PROCESS YOUR INFORMATION?</h5>
            <p>
              In Short: We process your information to provide, improve, and administer our Services, communicate with you, for security and fraud prevention, and to comply with law. We may also process your information for other purposes with your consent.
            </p>
            <p>We process your personal information for a variety of reasons, depending on how you interact with our Services, including:</p>
            <ul>
              <li>To facilitate account creation and authentication and otherwise manage user accounts. We may process your information so you can create and log in to your account, as well as keep your account in working order.</li>
              <li>To deliver and facilitate delivery of services to the user. We may process your information to provide you with the requested service.</li>
              <li>To respond to user inquiries/offer support to users. We may process your information to respond to your inquiries and solve any potential issues you might have with the requested service.</li>
              <li>To send administrative information to you. We may process your information to send you details about our products and services, changes to our terms and policies, and other similar information.</li>
              <li>To fulfill and manage your orders. We may process your information to fulfill and manage your orders, payments, returns, and exchanges made through the Services.</li>
              <li>To enable user-to-user communications. We may process your information if you choose to use any of our offerings that allow for communication with another user.</li>
              <li>To request feedback. We may process your information when necessary to request feedback and to contact you about your use of our Services.</li>
              <li>To send you marketing and promotional communications. We may process the personal information you send to us for our marketing purposes, if this is in accordance with your marketing preferences. You can opt out of our marketing emails at any time. For more information, see "WHAT ARE YOUR PRIVACY RIGHTS?" below.</li>
              <li>To deliver targeted advertising to you. We may process your information to develop and display personalized content and advertising tailored to your interests, location, and more. For more information see our Cookie Notice: <a href="http://www.siclarity.com/cookies">http://www.siclarity.com/cookies.</a></li>
              <li>To protect our Services. We may process your information as part of our efforts to keep our Services safe and secure, including fraud monitoring and prevention.</li>
              <li>To identify usage trends. We may process information about how you use our Services to better understand how they are being used so we can improve them.</li>
              <li>To determine the effectiveness of our marketing and promotional campaigns. We may process your information to better understand how to provide marketing and promotional campaigns that are most relevant to you.</li>
              <li>To save or protect an individual's vital interest. We may process your information when necessary to save or protect an individual's vital interest, such as to prevent harm.</li>
            </ul>
          </div>

          <div className="col-12">
            <h5 id="section3" >3. WHAT LEGAL BASES DO WE RELY ON TO PROCESS YOUR INFORMATION?</h5>
            <p>In Short: We only process your personal information when we believe it is necessary and we have a valid legal reason (i.e., legal basis) to do so under applicable law, like with your consent, to comply with laws, to provide you with services to enter into or fulfill our contractual obligations, to protect your rights, or to fulfill our legitimate business interests.</p>
            <p>
              If you are located in the EU or UK, this section applies to you.
            </p>
            <p>
              The General Data Protection Regulation (GDPR) and UK GDPR require us to explain the valid legal bases we rely on in order to process your personal information. As such, we may rely on the following legal bases to process your personal information:</p>
            <ul>
              <li>Consent. We may process your information if you have given us permission (i.e., consent) to use your personal information for a specific purpose. You can withdraw your consent at any time. Learn more about withdrawing your consent.</li>
              <li>Performance of a Contract. We may process your personal information when we believe it is necessary to fulfill our contractual obligations to you, including providing our Services or at your request prior to entering into a contract with you.</li>
              <li>Legitimate Interests. We may process your information when we believe it is reasonably necessary to achieve our legitimate business interests and those interests do not outweigh your interests and fundamental rights and freedoms. For example, we may process your personal information for some of the purposes described in order to:</li>
              <ul>
                <li>Send users information about special offers and discounts on our products and services</li>
                <li> Develop and display personalized and relevant advertising content for our users</li>
                <li>Analyze how our Services are used so we can improve them to engage and retain users</li>
                <li>Support our marketing activities</li>
                <li>Diagnose problems and/or prevent fraudulent activities</li>
                <li>Understand how our users use our products and services so we can improve user experience</li>
              </ul>
              <li>Legal Obligations. We may process your information where we believe it is necessary for compliance with our legal obligations, such as to cooperate with a law enforcement body or regulatory agency, exercise or defend our legal rights, or disclose your information as evidence in litigation in which we are involved.</li>
              <li>Vital Interests. We may process your information where we believe it is necessary to protect your vital interests or the vital interests of a third party, such as situations involving potential threats to the safety of any person.</li>
            </ul>
            <p>If you are located in Canada, this section applies to you.
            </p>
            <p>We may process your information if you have given us specific permission (i.e., express consent) to use your personal information for a specific purpose, or in situations where your permission can be inferred (i.e., implied consent). You can withdraw your consent at any time.</p>
            <p>In some exceptional cases, we may be legally permitted under applicable law to process your information without your consent, including, for example:</p>
            <ul>
              <li>If collection is clearly in the interests of an individual and consent cannot be obtained in a timely way</li>
              <li>For investigations and fraud detection and prevention</li>
              <li>For business transactions provided certain conditions are met</li>
              <li>If it is contained in a witness statement and the collection is necessary to assess, process, or settle an insurance claim</li>
              <li>For identifying injured, ill, or deceased persons and communicating with next of kin</li>
              <li>If we have reasonable grounds to believe an individual has been, is, or may be victim of financial abuse</li>
              <li>If it is reasonable to expect collection and use with consent would compromise the availability or the accuracy of the information and the collection is reasonable for purposes related to investigating a breach of an agreement or a contravention of the laws of Canada or a province</li>
              <li>If disclosure is required to comply with a subpoena, warrant, court order, or rules of the court relating to the production of records</li>
              <li>If it was produced by an individual in the course of their employment, business, or profession and the collection is consistent with the purposes for which the information was produced</li>
              <li>If the collection is solely for journalistic, artistic, or literary purposes</li>
              <li>If the information is publicly available and is specified by the regulations
              </li>
            </ul>
          </div>
          <div className="col-12">
            <h5 id="section4" >4. WHEN AND WITH WHOM DO WE SHARE YOUR PERSONAL INFORMATION?</h5>
            <p>
              In Short: We may share information in specific situations described in this section and/or with the following third parties.
            </p>
            <p>
              We may need to share your personal information in the following situations:
            </p>
            <ul>
              <li>Business Transfers. We may share or transfer your information in connection with, or during negotiations of, any merger, sale of company assets, financing, or acquisition of all or a portion of our business to another company.</li>
              <li>Affiliates. We may share your information with our affiliates, in which case we will require those affiliates to honor this Privacy Notice. Affiliates include our parent company and any subsidiaries, joint venture partners, or other companies that we control or that are under common control with us.</li>
              <li>Business Partners. We may share your information with our business partners to offer you certain products, services, or promotions.</li>
            </ul>
          </div>
        </div>
        <div className="col-12">
          <h5 id="section5">5. DO WE USE COOKIES AND OTHER TRACKING TECHNOLOGIES?
          </h5>
          <p>
            In Short: We may use cookies and other tracking technologies to collect and store your information.
          </p>
          <p>
            We may use cookies and similar tracking technologies (like web beacons and pixels) to gather information when you interact with our Services. Some online tracking technologies help us maintain the security of our Services and your account, prevent crashes, fix bugs, save your preferences, and assist with basic site functions.
          </p>
          <p>
            We also permit third parties and service providers to use online tracking technologies on our Services for analytics and advertising, including to help manage and display advertisements, to tailor advertisements to your interests, or to send abandoned shopping cart reminders (depending on your communication preferences). The third parties and service providers use their technology to provide advertising about products and services tailored to your interests which may appear either on our Services or on other websites.            </p>
          <p>To the extent these online tracking technologies are deemed to be a "sale"/"sharing" (which includes targeted advertising, as defined under the applicable laws) under applicable US state laws, you can opt out of these online tracking technologies by submitting a request as described below under section "DO UNITED STATES RESIDENTS HAVE SPECIFIC PRIVACY RIGHTS?"</p>
          <p>Specific information about how we use such technologies and how you can refuse certain cookies is set out in our Cookie Notice: <a href="http://www.siclarity.com/cookies">http://www.siclarity.com/cookies.</a></p>
          <h6>Google Analytics</h6>
          <p>We may share your information with Google Analytics to track and analyze the use of the Services. The Google Analytics Advertising Features that we may use include: Google Display Network Impressions Reporting and Google Analytics Demographics and Interests Reporting. To opt out of being tracked by Google Analytics across the Services, visit <a href="https://tools.google.com/dlpage/gaoptout">https://tools.google.com/dlpage/gaoptout</a>. You can opt out of Google Analytics Advertising Features through <a href="https://myadcenter.google.com/personalizationoff?sasb=true&ref=ad-settings">Ads Settings</a> and Ad Settings for mobile apps. Other opt out means include <a href="https://optout.networkadvertising.org/?c=1"> https://optout.networkadvertising.org/?c=1</a> and <a href="https://thenai.org/opt-out/mobile-opt-out/">http://www.networkadvertising.org/mobile-choice</a>. For more information on the privacy practices of Google, please visit the <a href="https://policies.google.com/privacy">Google Privacy & Terms page</a>.</p>
        </div>
        <div className="col-12">
          <h5 id="section6">6. HOW LONG DO WE KEEP YOUR INFORMATION?
          </h5>
          <p>
            In Short: We keep your information for as long as necessary to fulfill the purposes outlined in this Privacy Notice unless otherwise required by law.            </p>
          <p>
            We will only keep your personal information for as long as it is necessary for the purposes set out in this Privacy Notice, unless a longer retention period is required or permitted by law (such as tax, accounting, or other legal requirements). No purpose in this notice will require us keeping your personal information for longer than the period of time in which users have an account with us.            </p>
          <p>
            When we have no ongoing legitimate business need to process your personal information, we will either delete or anonymize such information, or, if this is not possible (for example, because your personal information has been stored in backup archives), then we will securely store your personal information and isolate it from any further processing until deletion is possible.            </p>
        </div>
        <div className="col-12">
          <h5 id="section7">7. HOW DO WE KEEP YOUR INFORMATION SAFE?</h5>
          <p>
            We reserve the right to update this Privacy Policy. Any changes will be posted within the App and on our website.
          </p>
          <p>
            In Short: We aim to protect your personal information through a system of organizational and technical security measures.            </p>
          <p>
            We have implemented appropriate and reasonable technical and organizational security measures designed to protect the security of any personal information we process. However, despite our safeguards and efforts to secure your information, no electronic transmission over the Internet or information storage technology can be guaranteed to be 100% secure, so we cannot promise or guarantee that hackers, cybercriminals, or other unauthorized third parties will not be able to defeat our security and improperly collect, access, steal, or modify your information. Although we will do our best to protect your personal information, transmission of personal information to and from our Services is at your own risk. You should only access the Services within a secure environment.            </p>
        </div>
        <div className="col-12">
          <h5 id="section8">8. DO WE COLLECT INFORMATION FROM MINORS?
          </h5>
          <p>
            In Short: We do not knowingly collect data from or market to children under 18 years of age.
          </p>
          <p>
            We do not knowingly collect, solicit data from, or market to children under 18 years of age, nor do we knowingly sell such personal information. By using the Services, you represent that you are at least 18 or that you are the parent or guardian of such a minor and consent to such minor dependent's use of the Services. If we learn that personal information from users less than 18 years of age has been collected, we will deactivate the account and take reasonable measures to promptly delete such data from our records. If you become aware of any data we may have collected from children under age 18, please contact us at contact@siclarity.com.            </p>
        </div>
        <div className="col-12">
          <h5 id="section9">9. WHAT ARE YOUR PRIVACY RIGHTS?</h5>
          <p>
            In Short: Depending on your state of residence in the US or in some regions, such as the European Economic Area (EEA), United Kingdom (UK), Switzerland, and Canada, you have rights that allow you greater access to and control over your personal information. You may review, change, or terminate your account at any time, depending on your country, province, or state of residence.            </p>
          <p>
            In some regions (like the EEA, UK, Switzerland, and Canada), you have certain rights under applicable data protection laws. These may include the right (i) to request access and obtain a copy of your personal information, (ii) to request rectification or erasure; (iii) to restrict the processing of your personal information; (iv) if applicable, to data portability; and (v) not to be subject to automated decision-making. In certain circumstances, you may also have the right to object to the processing of your personal information. You can make such a request by contacting us by using the contact details provided in the section <a href="#section13">"HOW CAN YOU CONTACT US ABOUT THIS NOTICE?"</a> below. </p>
          <p>
            We will consider and act upon any request in accordance with applicable data protection laws.
          </p>
          <p>If you are located in the EEA or UK and you believe we are unlawfully processing your personal information, you also have the right to complain to your <a href="https://ec.europa.eu/newsroom/article29/items/612080">Member State data protection authority</a> or <a href="https://ico.org.uk/make-a-complaint/data-protection-complaints/">UK data protection authority</a>.</p>
          <p>If you are located in Switzerland, you may contact the<a href="https://www.edoeb.admin.ch/edoeb/en/home.html">Federal Data Protection and Information Commissioner</a>.
          </p>
          <p>Withdrawing your consent: If we are relying on your consent to process your personal information, which may be express and/or implied consent depending on the applicable law, you have the right to withdraw your consent at any time. You can withdraw your consent at any time by contacting us by using the contact details provided in the section <a href="#section13">"HOW CAN YOU CONTACT US ABOUT THIS NOTICE?"</a> below.</p>
          <p>However, please note that this will not affect the lawfulness of the processing before its withdrawal nor, when applicable law allows, will it affect the processing of your personal information conducted in reliance on lawful processing grounds other than consent.</p>
          <p>Opting out of marketing and promotional communications: You can unsubscribe from our marketing and promotional communications at any time by clicking on the unsubscribe link in the emails that we send, or by contacting us using the details provided in the section<a href="#section13">"HOW CAN YOU CONTACT US ABOUT THIS NOTICE?"</a> below. You will then be removed from the marketing lists. However, we may still communicate with you - for example, to send you service-related messages that are necessary for the administration and use of your account, to respond to service requests, or for other non-marketing purposes.</p>
          <h6>Account Information</h6>
          <p>If you would at any time like to review or change the information in your account or terminate your account, you can:
          </p>
          <ul>
            <li>Contact us using the contact information provided.</li>
            <li> Log in to your account settings and update your user account.</li>
          </ul>
          <p>Upon your request to terminate your account, we will deactivate or delete your account and information from our active databases. However, we may retain some information in our files to prevent fraud, troubleshoot problems, assist with any investigations, enforce our legal terms and/or comply with applicable legal requirements.</p>
          <p>Cookies and similar technologies: Most Web browsers are set to accept cookies by default. If you prefer, you can usually choose to set your browser to remove cookies and to reject cookies. If you choose to remove cookies or reject cookies, this could affect certain features or services of our Services. For further information, please see our Cookie Notice: <a href="https://www.siclarity.com/cookies"> http://www.siclarity.com/cookies</a>.</p>
          <p>If you have questions or comments about your privacy rights, you may email us at contact@siclarity.com</p>
        </div>
        <div className="col-12">
          <h5 id="section10">10. CONTROLS FOR DO-NOT-TRACK FEATURES</h5>
          <p>Most web browsers and some mobile operating systems and mobile applications include a Do-Not-Track ("DNT") feature or setting you can activate to signal your privacy preference not to have data about your online browsing activities monitored and collected. At this stage, no uniform technology standard for recognizing and implementing DNT signals has been finalized. As such, we do not currently respond to DNT browser signals or any other mechanism that automatically communicates your choice not to be tracked online. If a standard for online tracking is adopted that we must follow in the future, we will inform you about that practice in a revised version of this Privacy Notice.</p>
          <p>California law requires us to let you know how we respond to web browser DNT signals. Because there currently is not an industry or legal standard for recognizing or honoring DNT signals, we do not respond to them at this time.</p>
        </div>
        <div className="col-12">
          <h5 id="section11">11. DO UNITED STATES RESIDENTS HAVE SPECIFIC PRIVACY RIGHTS?
          </h5>
          <p>In Short: If you are a resident of California, Colorado, Connecticut, Delaware, Florida, Indiana, Iowa, Kentucky, Minnesota, Montana, Nebraska, New Hampshire, New Jersey, Oregon, Tennessee, Texas, Utah, or Virginia, you may have the right to request access to and receive details about the personal information we maintain about you and how we have processed it, correct inaccuracies, get a copy of, or delete your personal information. You may also have the right to withdraw your consent to our processing of your personal information. These rights may be limited in some circumstances by applicable law. More information is provided below.</p>
          <h6>Categories of Personal Information We Collect</h6>
          <p>We have collected the following categories of personal information in the past twelve (12) months:</p>
          <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid black' }}>
            <thead>
              <tr>
                <th style={{ width: '33.8%', textAlign: 'left', border: '1px solid black', padding: '8px' }}>Category</th>
                <th style={{ width: '51.4%', textAlign: 'left', border: '1px solid black', padding: '8px' }}>Examples</th>
                <th style={{ width: '14.9%', textAlign: 'center', border: '1px solid black', padding: '8px' }}>Collected</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>A. Identifiers</td>
                <td style={{ border: '1px solid black', padding: '8px' }}>
                  Contact details, such as real name, alias, postal address, telephone or mobile contact number, unique personal identifier, online identifier, Internet Protocol address, email address, and account name
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>YES</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>B. Personal information as defined in the California Customer Records statute</td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Name, contact information, education, employment, employment history, and financial information
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>YES</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>C. Protected classification characteristics under state or federal law
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Gender, age, date of birth, race and ethnicity, national origin, marital status, and other demographic data
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>D. Commercial information
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Transaction information, purchase history, financial details, and payment information
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
               <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>E. Biometric information
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Fingerprints and voiceprints
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>F. Internet or other similar network activity
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Browsing history, search history, online behavior, interest data, and interactions with our and other websites, applications, systems, and advertisements
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>G. Geolocation data
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Device location
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>H. Audio, electronic, sensory, or similar information
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Images and audio, video or call recordings created in connection with our business activities
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>I. Professional or employment-related information
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Business contact details in order to provide you our Services at a business level or job title, work history, and professional qualifications if you apply for a job with us
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>YES</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>J. Education Information
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Student records and directory information
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>K. Inferences drawn from collected personal information
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>Inferences drawn from any of the collected personal information listed above to create a profile or summary about, for example, an individual’s preferences and characteristics
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid black', padding: '8px' }}>L. Sensitive personal Information
                </td>
                <td style={{ border: '1px solid black', padding: '8px' }}>
                </td>
                <td style={{ border: '1px solid black', textAlign: 'center', padding: '8px' }}>NO</td>
              </tr>
            </tbody>
          </table>
          <p>We may also collect other personal information outside of these categories through instances where you interact with us in person, online, or by phone or mail in the context of:</p>
          <ul>
            <li>Receiving help through our customer support channels;</li>
            <li>Participation in customer surveys or contests; and</li>
            <li>Facilitation in the delivery of our Services and to respond to your inquiries.</li>
          </ul>
          <p>
            We will use and retain the collected personal information as needed to provide the Services or for:
          </p>
          <ul>
            <li>Category A - As long as the user has an account with us</li>
            <li>Category B - As long as the user has an account with us</li>
            <li>Category H - As long as the user has an account with us</li>
            <li>Category I - As long as the user has an account with us</li>
          </ul>
          <h6>Sources of Personal Information</h6>
          <p>Learn more about the sources of personal information we collect in <a href="#section1">"WHAT INFORMATION DO WE COLLECT?"</a></p>
          <h6> How We Use and Share Personal Information</h6>
          <p>Learn more about how we use your personal information in the section,<a href="#section2">"HOW DO WE PROCESS YOUR INFORMATION?"</a>
            Will your information be shared with anyone else?</p>
          <p>We may disclose your personal information with our service providers pursuant to a written contract between us and each service provider. Learn more about how we disclose personal information to in the section, <a href="#section5">"WHEN AND WITH WHOM DO WE SHARE YOUR PERSONAL INFORMATION?"</a></p>
          <p>We may use your personal information for our own business purposes, such as for undertaking internal research for technological development and demonstration. This is not considered to be "selling" of your personal information.</p>
          <p>We have not disclosed, sold, or shared any personal information to third parties for a business or commercial purpose in the preceding twelve (12) months. We will not sell or share personal information in the future belonging to website visitors, users, and other consumers.</p>
          <h6>Your Rights</h6>
          <p>You have rights under certain US state data protection laws. However, these rights are not absolute, and in certain cases, we may decline your request as permitted by law. These rights include:</p>
          <ul>
            <li>Right to know whether or not we are processing your personal data</li>
            <li> Right to access your personal data</li>
            <li>Right to correct inaccuracies in your personal data</li>
            <li> Right to request the deletion of your personal data</li>
            <li>Right to obtain a copy of the personal data you previously shared with us</li>
            <li>Right to non-discrimination for exercising your rights</li>
            <li>Right to opt out of the processing of your personal data if it is used for targeted advertising (or sharing as defined under California's privacy law), the sale of personal data, or profiling in furtherance of decisions that produce legal or similarly significant effects ("profiling")
            </li>
          </ul>
          <p>Depending upon the state where you live, you may also have the following rights:
          </p>
          <ul>
            <li>Right to access the categories of personal data being processed (as permitted by applicable law, including Minnesota's privacy law)</li>
            <li>Right to obtain a list of the categories of third parties to which we have disclosed personal data (as permitted by applicable law, including California's and Delaware's privacy law)</li>
            <li>Right to obtain a list of specific third parties to which we have disclosed personal data (as permitted by applicable law, including Minnesota's and Oregon's privacy law)</li>
            <li>Right to review, understand, question, and correct how personal data has been profiled (as permitted by applicable law, including Minnesota’s privacy law)</li>
            <li>Right to review, understand, question, and correct how personal data has been profiled (as permitted by applicable law, including Minnesota’s privacy law)</li>
            <li>Right to limit use and disclosure of sensitive personal data (as permitted by applicable law, including California’s privacy law)</li>
            <li>Right to opt out of the collection of sensitive data and personal data collected through the operation of a voice or facial recognition feature (as permitted by applicable law, including Florida’s privacy law)</li>
          </ul>
          <h6>How to Exercise Your Rights
          </h6>
          <p>To exercise these rights, you can contact us by submitting a <a href="https://app.termly.io/notify/e004b96c-767a-4b62-8a3e-8a2fd0405313">data subject access request</a>, by emailing us at contact@siclarity.com, or by referring to the contact details at the bottom of this document.</p>
          <p>We will honor your opt-out preferences if you enact the <a href="https://globalprivacycontrol.org/"> Global Privacy Control</a> (GPC) opt-out signal on your browser.
          </p>
          <p>Under certain US state data protection laws, you can designate an authorized agent to make a request on your behalf. We may deny a request from an authorized agent that does not submit proof that they have been validly authorized to act on your behalf in accordance with applicable laws.</p>
          <h6>Request Verification
          </h6>
          <p>Upon receiving your request, we will need to verify your identity to determine you are the same person about whom we have the information in our system. We will only use personal information provided in your request to verify your identity or authority to make the request. However, if we cannot verify your identity from the information already maintained by us, we may request that you provide additional information for the purposes of verifying your identity and for security or fraud-prevention purposes.</p>
          <p>If you submit the request through an authorized agent, we may need to collect additional information to verify your identity before processing your request and the agent will need to provide a written and signed permission from you to submit such request on your behalf.</p>
          <h6>Appeals</h6>
          <p>Under certain US state data protection laws, if we decline to take action regarding your request, you may appeal our decision by emailing us at </p>
          <h6>California "Shine The Light"</h6>
          <p>California Civil Code Section 1798.83, also known as the "Shine The Light"  law, permits our users who are California residents to request and obtain from us, once a year and free of charge, information about categories of personal information (if any) we disclosed to third parties for direct marketing purposes and the names and addresses of all third parties with which we shared personal information in the immediately preceding calendar year. If you are a California resident and would like to make such a request, please submit your request in writing to us by using the contact details provided in the section <a href="#section13"> "HOW CAN YOU CONTACT US ABOUT THIS NOTICE?"</a></p>
        </div>
        <div className="col-12">
          <h5 id="section12">12. DO WE MAKE UPDATES TO THIS NOTICE?</h5>
          <p>In Short: Yes, we will update this notice as necessary to stay compliant with relevant laws.
          </p>
          <p>We may update this Privacy Notice from time to time. The updated version will be indicated by an updated "Revised" date at the top of this Privacy Notice. If we make material changes to this Privacy Notice, we may notify you either by prominently posting a notice of such changes or by directly sending you a notification. We encourage you to review this Privacy Notice frequently to be informed of how we are protecting your information.</p>
        </div>
        <div className="col-12">
          <h5 id="section13" >13. HOW CAN YOU CONTACT US ABOUT THIS NOTICE?
          </h5>
          <p>If you have questions or comments about this notice, you may email us at contact@siclarity.com or contact us by post at:
          </p>
          <p>SiClarity, Inc. <br />
            333 West Maude Avenue <br />
            Suite 207 <br />
            Sunnyvale, CA 94085 <br />
            United States</p>
        </div>
        <div className="col-12">
          <h5 id="section14">14. HOW CAN YOU REVIEW, UPDATE, OR DELETE THE DATA WE COLLECT FROM YOU?
          </h5>
          <p className="mb-0 pb-4">Based on the applicable laws of your country or state of residence in the US, you may have the right to request access to the personal information we collect from you, details about how we have processed it, correct inaccuracies, or delete your personal information. You may also have the right to withdraw your consent to our processing of your personal information. These rights may be limited in some circumstances by applicable law. To request to review, update, or delete your personal information, please fill out and submit a <a href="https://app.termly.io/notify/e004b96c-767a-4b62-8a3e-8a2fd0405313">data subject access request.</a>
          </p>
        </div> 
      </div>
    </>
  );
}

export default PrivacyPolicy;
