using System;
using System.Collections;
using System.Collections.Generic;

using UnityEngine;
using UnityEngine.UI;

using TMPro;

public class TitleUIController : Singleton<TitleUIController> 
{
    [Header("ReadyZone")]
    [SerializeField] private GameObject readyZoneObj;
    [SerializeField] private GameObject r_logMsgObj;
    private TMP_Text r_logMsgTxt;
    [SerializeField] private TMP_Text r_nicknameTxt;
    [SerializeField] private TMP_Text r_levelTxt;
    [SerializeField] private Button r_gameStartBtn;
    [SerializeField] private Button r_signOutBtn;



    [Space][Header("ConnectionZone")]
    [SerializeField] private GameObject connectionZoneObj;
    [SerializeField] private GameObject c_logMsgObj;
    private TMP_Text c_logMsgTxt;
    [SerializeField] private TMP_Text c_nicknameInputTxt;
    [SerializeField] private Button c_signInBtn;



    // button action
    public event Action GameStartProc;
    public event Action SignInProc;
    public event Action SignOutProc;



    // etc
    private GameObject nowLogObj;
    private TMP_Text nowLogTxt;



    private void Start()
    {
        // ready zone
        r_logMsgTxt = r_logMsgObj.GetComponent<TMP_Text>();

        r_gameStartBtn.onClick.AddListener(() => GameStartProc());
        r_signOutBtn.onClick.AddListener(() => SignOutProc());


        // connection zone
        c_logMsgTxt = c_logMsgObj.GetComponent<TMP_Text>();

        c_signInBtn.onClick.AddListener(() => SignInProc());
    }



    public void ShowReadyZone(string nickname, int lv)
    {
        r_nicknameTxt.text = nickname;
        r_levelTxt.text = $"Lv.{lv}";

        nowLogObj = r_logMsgObj;
        nowLogTxt = r_logMsgTxt;
        UpdateLog();

        readyZoneObj.SetActive(true);
        connectionZoneObj.SetActive(false);
    }
    public void ShowConnectionZone()
    {
        c_nicknameInputTxt.text = "";

        nowLogObj = c_logMsgObj;
        nowLogTxt = c_logMsgTxt;
        UpdateLog();

        readyZoneObj.SetActive(false);
        connectionZoneObj.SetActive(true);
    }


    public void UpdateLog(string log = "")
    {
        nowLogTxt.text = log;
        nowLogObj.SetActive(!string.Equals(log, "", StringComparison.Ordinal));
    }
}
