from django.db import models

# Create your models here.

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class_type_choices=(
                    ('online',u'网络班'),
                    ('offline_weekend',u'面授班(周末)'),
                    ('offline_fulltime',u'面授班(脱产)',)
                    )


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    name = models.CharField(u'姓名',max_length=32)
    email = models.EmailField(u'邮箱',max_length=60,blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'用户信息'
        verbose_name_plural = verbose_name


class School(models.Model):
    name = models.CharField(u"校区名称",max_length=64,unique=True)
    addr = models.CharField(u"地址", max_length=128)
    staffs = models.ManyToManyField('UserProfile', blank=True)
    # 有多个员工，一个多对多的关联

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'校区'
        verbose_name_plural = verbose_name


class Course(models.Model):
    name = models.CharField(u"课程名称", max_length=128, unique=True)
    price = models.IntegerField(u"面授价格")
    online_price = models.IntegerField(u"网络班价格")
    brief = models.TextField(u"课程简介")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'课程名称'
        verbose_name_plural = u'课程名称'


class ClassList(models.Model):
    course = models.ForeignKey('Course')
    # 班级与课程关联
    course_type = models.CharField(u"课程类型", choices=class_type_choices, max_length=32)
    semester = models.IntegerField(u"学期")
    start_date = models.DateField(u"开班日期")
    graduate_date = models.DateField(u"结业日期", blank=True, null=True)
    teachers = models.ManyToManyField(UserProfile, verbose_name=u"讲师")

    def __str__(self):
        # return "%s(%s)[%s]" %(self.course.name,self.course_type,self.semester)        #注意上面这个返回的结果是"Python自动化开发(offline_weekend)[14]"为了谁页面上将offline_weekend显示成中文应按照下面的写法
        return "%s(%s)[%s]" % (self.course.name, self.get_course_type_display(), self.semester)

    class Meta:
        verbose_name = u'班级列表'
        verbose_name_plural = u"班级列表"
        unique_together = ("course", "course_type", "semester")  # 联合唯一这三个加起来要是唯一的，不能说一个课程多个12期


class Customer(models.Model):
    qq = models.CharField(u"QQ号", max_length=64, unique=True)  # QQ是必须值unique=True
    name = models.CharField(u"姓", max_length=32, blank=True, null=True)  # 名字可以为空
    phone = models.BigIntegerField(u'手机号', blank=True, null=True)
    # 手机号也可以为空
    stu_id = models.CharField(u"学号", blank=True, null=True, max_length=64)
    # 入学后才会有的学号
    # id = models.CharField(u"身份证号",blank=True,null=True,max_length=128)
    source_type = (('qq', u"qq群"),
                   ('referral', u"内部转介绍"),
                   ('51cto', u"51cto"),
                   ('agent', u"招生代理"),
                   ('others', u"其它"),
                   )
    # 客户来源
    source = models.CharField(u'客户来源', max_length=64, choices=source_type, default='qq')
    # 直接可选默认来源为QQ
    referral_from = models.ForeignKey('self', verbose_name=u"转介绍自学员", help_text=u"若此客户是转介绍自内部学员,请在此处选择内部学员姓名",
                                      blank=True, null=True, related_name="internal_referral")
    # 学员可以来自内部学员，而内部学员当然也是客户，所以这个外键关联就存在自关联的问题，即关联自己用‘slef’代替，verbose_name表示在admin页面显示成啥样，help_text提示信息，related_name="internal_referral"只要是外键关联自己一定要写该值
    course = models.ForeignKey(Course, verbose_name=u"咨询课程")
    class_type = models.CharField(u"班级类型", max_length=64, choices=class_type_choices)
    customer_note = models.TextField(u"客户咨询内容详情", help_text=u"客户咨询的大概情况,客户个人信息备注等...")
    status_choices = (('signed', u"已报名"),
                      ('unregistered', u"未报名"),
                      ('graduated', u"已毕业"),
                      )
    status = models.CharField(u"状态", choices=status_choices, max_length=64, default=u"unregistered",
                              help_text=u"选择客户此时的状态")
    consultant = models.ForeignKey(UserProfile, verbose_name=u"课程顾问")
    date = models.DateField(u"咨询日期", auto_now_add=True)
    class_list = models.ManyToManyField('ClassList', verbose_name=u"已报班级", blank=True)

    def __str__(self):
        return "%s,%s" % (self.qq, self.name)

    class Meta:
        verbose_name = u'客户信息'
        verbose_name_plural = u'客户信息'


class ConsultRecord(models.Model):
    customer = models.ForeignKey(Customer, verbose_name=u"所咨询客户")
    note = models.TextField(u"跟进内容...")
    status_choices = ((1, u"近期无报名计划"),
                      (2, u"2个月内报名"),
                      (3, u"1个月内报名"),
                      (4, u"2周内报名"),
                      (5, u"1周内报名"),
                      (6, u"2天内报名"),
                      (7, u"已报名"),
                      )
    status = models.IntegerField(u"状态", choices=status_choices, help_text=u"选择客户此时的状态")
    consultant = models.ForeignKey(UserProfile, verbose_name=u"跟踪人")
    date = models.DateField(u"跟进日期", auto_now_add=True)

    def __str__(self):
        return u"%s, %s" % (self.customer, self.status)

    class Meta:
        verbose_name = u'客户咨询跟进记录'
        verbose_name_plural = u"客户咨询跟进记录"


class CourseRecord(models.Model):
    '''教师生成上课记录'''
    course = models.ForeignKey(ClassList, verbose_name=u"班级(课程)")
    day_num = models.IntegerField(u"节次", help_text=u"此处填写第几节课或第几天课程...,必须为数字")
    date = models.DateField(auto_now_add=True, verbose_name=u"上课日期")
    # 自动添加日期
    teacher = models.ForeignKey(UserProfile, verbose_name=u"讲师")

    def __str__(self):
        return u"%s 第%s天" % (self.course, self.day_num)

    class Meta:
        verbose_name = u'上课记录'
        verbose_name_plural = u"上课记录"
        unique_together = ('course', 'day_num')


class StudyRecord(models.Model):
    '''记录上课学生'''
    course_record = models.ForeignKey(CourseRecord,
                                      verbose_name=u"第几天课程")  # 关联课程，这天的课程可以很多人关联，如果是onetoone则便是一个人关联该课程其他人也没有资格关联了
    student = models.ForeignKey(Customer, verbose_name=u"学员")
    record_choices = (('checked', u"已签到"),
                      ('late', u"迟到"),
                      ('noshow', u"缺勤"),
                      ('leave_early', u"早退"),
                      )
    record = models.CharField(u"上课记录", choices=record_choices, default="checked", max_length=64)
    score_choices = ((100, 'A+'),
                     (90, 'A'),
                     (85, 'B+'),
                     (80, 'B'),
                     (70, 'B-'),
                     (60, 'C+'),
                     (50, 'C'),
                     (40, 'C-'),
                     (0, 'D'),
                     (-1, 'N/A'),
                     (-100, 'COPY'),
                     (-1000, 'FAIL'),
                     )
    score = models.IntegerField(u"本节成绩", choices=score_choices, default=-1)
    date = models.DateTimeField(auto_now_add=True)
    note = models.CharField(u"备注", max_length=255, blank=True, null=True)

    def __str__(self):
        return u"%s,学员:%s,记录:%s, 成绩:%s" % (self.course_record, self.student.name, self.record, self.get_score_display())

    class Meta:
        verbose_name = u'学员学习纪录'
        verbose_name_plural = u"学员学习纪录"
        unique_together = ('course_record', 'student')  # 在一个18天学生只能上一次课

